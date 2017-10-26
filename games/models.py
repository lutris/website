"""Models for main lutris app"""

from copy import copy
import datetime
# pylint: disable=E1002, E0202
import re
import json
import random
from itertools import chain

import six
import reversion
import yaml
from bitfield import BitField
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.text import slugify
from reversion.models import Version

from common.util import get_auto_increment_slug
from emails import messages
from games import managers
from games.util import steam
from platforms.models import Platform
from runners.models import Runner

DEFAULT_INSTALLER = {
    'files': [
        {'file_id': "http://location"},
        {'unredistribuable_file': "N/A"}
    ],
    'installer': [
        {'move': {'src': 'file_id', 'dst': '$GAMEDIR'}}
    ]
}


class Company(models.Model):
    """Gaming company"""
    name = models.CharField(max_length=127)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='companies/logos', blank=True)
    website = models.CharField(max_length=128, blank=True)

    # pylint: disable=W0232, R0903
    class Meta(object):
        """Additional configuration for model"""
        verbose_name_plural = "companies"
        ordering = ['name']

    def get_absolute_url(self):
        return reverse("games_by_company", args=(self.slug, ))

    def __unicode__(self):
        return u"%s" % self.name

    def save(self, force_insert=True, using=None):
        self.slug = slugify(self.name)
        if not self.slug:
            raise ValueError("Tried to save Company without a slug: %s", self)
        return super(Company, self).save(force_insert=force_insert, using=using)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', 'slug__icontains')


class Genre(models.Model):
    """Gaming genre"""
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    objects = managers.GenreManager()

    # pylint: disable=W0232, R0903
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def save(self, force_insert=True, using=None):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Genre, self).save(force_insert=force_insert, using=using)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', )


class GameManager(models.Manager):
    def published(self):
        return self.get_queryset().filter(change_for__isnull=True).filter(is_public=True)

    def with_installer(self):
        return (
            self.get_queryset()
            .filter(change_for__isnull=True)
            .filter(is_public=True)
            .filter(
                Q(installers__published=True) |
                Q(platforms__default_installer__startswith='{')
            )
            .order_by('name')
            .annotate(installer_count=Count('installers'))
            .annotate(default_installer_count=Count('platforms'))
        )

    def get_random(self, option=""):
        if not re.match('^[\w\d-]+$', option) or len(option) > 128:
            return
        pk_query = self.get_queryset()
        if option == 'incomplete':
            pk_query = pk_query.filter(change_for__isnull=True).filter(year=None)
        elif option == 'published':
            pk_query = self.with_installer()
        elif len(option) > 1:
            pk_query = pk_query.filter(
                Q(platforms__slug=option) |
                Q(installers__runner__slug=option)
            )
        pks = pk_query.values_list('pk', flat=True)
        random_pk = random.choice(pks)
        return self.get_queryset().get(pk=random_pk)


class Game(models.Model):
    """Game model"""
    GAME_FLAGS = (
        ('fully_libre', 'Fully libre'),
        ('open_engine', 'Open engine only'),
        ('free', 'Free'),
        ('freetoplay', 'Free-to-play'),
        ('pwyw', 'Pay what you want'),
        ('demo', 'Has a demo'),
        ('protected', 'Installer modification is restricted'),
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    platforms = models.ManyToManyField(Platform)
    genres = models.ManyToManyField(Genre)
    publisher = models.ForeignKey(
        Company, related_name='published_game', null=True, blank=True
    )
    developer = models.ForeignKey(
        Company, related_name='developed_game', null=True, blank=True
    )
    website = models.CharField(max_length=200, blank=True)
    icon = models.ImageField(upload_to='games/icons', blank=True)
    title_logo = models.ImageField(upload_to='games/banners', blank=True)
    description = models.TextField(blank=True)
    is_public = models.BooleanField("Published", default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    steamid = models.PositiveIntegerField(null=True, blank=True)
    gogslug = models.CharField(max_length=200, blank=True)
    gogid = models.PositiveIntegerField(null=True, unique=True)
    humblestoreid = models.CharField(max_length=200, blank=True)
    flags = BitField(flags=GAME_FLAGS)

    # Indicates whether this data row is a changeset for another data row.
    # If so, this attribute is not NULL and the value is the ID of the
    # corresponding data row
    change_for = models.ForeignKey('self', null=True, blank=True)

    objects = GameManager()

    # pylint: disable=W0232, R0903
    class Meta(object):
        ordering = ['name']
        permissions = (
            ('can_publish_game', "Can publish game"),
        )

    def __unicode__(self):
        if self.change_for is None:
            return self.name
        else:
            return '[Changes for] ' + self.change_for.name

    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains",)

    @property
    def banner_url(self):
        if self.title_logo:
            return reverse('get_banner', kwargs={'slug': self.slug})

    @property
    def icon_url(self):
        if self.icon:
            return reverse('get_icon', kwargs={'slug': self.slug})

    @property
    def flag_labels(self):
        """Return labels of active flags, suitable for display"""
        return [self.flags.get_label(flag[0]) for flag in self.flags if flag[1]]

    def create_copy(self):
        """Creates a shallow copy of this model"""
        return copy(self)

    def prepare_change_submission(self, change_for):
        """Prepares a change submission. Needs to be called before save()"""

        self.id = None
        self.pk = None
        self.slug = None
        self.is_public = False
        self.change_for = change_for

    def get_changes(self):
        """Returns a dictionary of the changes"""

        changes = []
        considered_entries = ['name', 'year', 'platforms', 'genres', 'website', 'description']

        # From the considered fields, only those who differ will
        # be returned
        for entry in considered_entries:
            old_value = getattr(self.change_for, entry)
            new_value = getattr(self, entry)

            # M2M relations to string
            if entry in ['platforms', 'genres']:
                old_value = ', '.join('[{0}]'.format(str(x)) for x in list(old_value.all()))
                new_value = ', '.join('[{0}]'.format(str(x)) for x in list(new_value.all()))

            if old_value != new_value:
                changes.append((entry, old_value, new_value))

        return changes

    def apply_changes(self, change_set):
        """Applies user-suggested changes to this model"""

        self.name = change_set.name
        self.year = change_set.year
        self.platforms.set(change_set.platforms.all())
        self.genres.set(change_set.genres.all())
        self.website = change_set.website
        self.description = change_set.description

    def has_installer(self):
        return self.installers.exists() or self.has_auto_installers()

    def has_auto_installers(self):
        return self.platforms.filter(default_installer__isnull=False).exists()

    def get_absolute_url(self):
        """Return the absolute url for a game"""
        return reverse("game_detail", kwargs={'slug': self.slug})

    def download_steam_capsule(self):
        if self.title_logo or not self.steamid:
            return
        else:
            self.title_logo = ContentFile(steam.get_capsule(self.steamid),
                                          "%d.jpg" % self.steamid)

    def get_steam_logo(self, img_url):
        self.title_logo = ContentFile(steam.get_image(self.steamid, img_url),
                                      "%d.jpg" % self.steamid)

    def get_steam_icon(self, img_url):
        self.icon = ContentFile(steam.get_image(self.steamid, img_url),
                                "%d.jpg" % self.steamid)

    def steam_support(self):
        """ Return the platform supported by Steam """
        if not self.steamid:
            return False
        platforms = [p.slug for p in self.platforms.all()]
        if 'linux' in platforms:
            return 'linux'
        elif 'windows' in platforms:
            return 'windows'
        return True

    def get_default_installers(self):
        installers = []
        for platform in self.platforms.all():
            if platform.default_installer:
                installer = platform.default_installer
                installer['name'] = self.name
                installer['game_slug'] = self.slug
                installer['version'] = platform.name
                installer['slug'] = "-".join((self.slug[:30],
                                              platform.slug[:20]))
                installer['platform'] = platform.slug
                installer['description'] = ""
                installer['published'] = True
                installer['auto'] = True
                installers.append(installer)
        return installers

    def check_for_submission(self):
        # Skip freshly created and unpublished objects
        if not self.pk or not self.is_public:
            return

        # Skip objects that were already published
        original = Game.objects.get(pk=self.pk)
        if original.is_public:
            return

        try:
            submission = GameSubmission.objects.get(game=self,
                                                    accepted_at__isnull=True)
        except GameSubmission.DoesNotExist:
            pass
        else:
            submission.accept()

    def save(self, force_insert=True, using=None):
        if not self.change_for:
            if not self.slug:
                self.slug = slugify(self.name)[:50]
            if not self.slug:
                raise ValueError("Can't generate a slug for name %s" % self.name)
            self.download_steam_capsule()
            self.check_for_submission()
        return super(Game, self).save()


class GameMetadata(models.Model):
    game = models.ForeignKey(Game)
    key = models.CharField(max_length=16)
    value = models.CharField(max_length=255)


class Screenshot(models.Model):
    """Screenshots for games"""
    game = models.ForeignKey(Game)
    image = models.ImageField(upload_to="games/screenshots")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    description = models.CharField(max_length=256, null=True, blank=True)
    published = models.BooleanField(default=False)

    objects = managers.ScreenshotManager()

    def __unicode__(self):
        desc = self.description if self.description else self.game.name
        return u"%s: %s (uploaded by %s)" % (self.game, desc, self.uploaded_by)


class InstallerManager(models.Manager):
    def published(self):
        return self.get_queryset().filter(published=True)

    def unpublished(self):
        return self.get_queryset().filter(published=False)

    def abandoned(self):
        """Return the installer with 'Change Me' version that haven't received any modifications"""
        return [
            installer for installer in self.get_queryset().filter(version='Change Me')
            if not Version.objects.filter(object_id=installer.id, content_type__model='installer').count()
        ]

    def _fuzzy_search(self, slug, return_models=False):
        try:
            # Try returning installers by installer slug
            installer = self.get_queryset().get(slug=slug)
            return [installer]
        except ObjectDoesNotExist:

            # Try getting installers by game name
            try:
                game = Game.objects.get(slug=slug)
            except ObjectDoesNotExist:
                game = None

            if game:
                installers = self.get_queryset().filter(game=game, published=True)

                auto_installers = []
                for platform in game.platforms.exclude(default_installer__isnull=True):
                    auto_installers.append(AutoInstaller(game, platform))

                if installers or auto_installers:
                    return list(chain(installers, auto_installers))

            # Try auto installers
            for platform in Platform.objects.exclude(default_installer__isnull=True):
                suffix = "-" + platform.slug
                if slug.endswith(suffix):
                    game_slug = slug[:-len(suffix)]
                    try:
                        game = Game.objects.get(slug=game_slug)
                    except Game.DoesNotExist:
                        pass
                    else:
                        if return_models:
                            try:
                                auto_installer = AutoInstaller(game, platform)
                                if auto_installer.slug == slug:
                                    return [auto_installer]
                            except ObjectDoesNotExist:
                                pass
                        else:
                            auto_installers = game.get_default_installers()
                            for auto_installer in auto_installers:
                                if auto_installer['slug'] == slug:
                                    return [auto_installer]

            # A bit hackish, return_models is used for filter and not with get
            if return_models:
                return self.none()
            else:
                raise

    def fuzzy_get(self, slug):
        """Return either the installer that matches exactly 'slug' or the
        installers with game matching slug.
        Installers are always returned in a list.
        TODO: Deprecate in favor of fuzzy_filter
        """
        return self._fuzzy_search(slug)

    def fuzzy_filter(self, slug):
        """Like fuzzy_get but always returns a list of model instances"""
        return self._fuzzy_search(slug, return_models=True)

    def get_json(self, slug):
        try:
            installers = self.fuzzy_get(slug)
        except ObjectDoesNotExist:
            installer_data = []
        else:
            if installers and isinstance(installers[0], dict):
                installer_data = installers
            else:
                installer_data = [installer.as_dict()
                                  for installer in installers]
        try:
            game = Game.objects.get(slug=slug)
            installer_data += game.get_default_installers()
        except ObjectDoesNotExist:
            pass
        if not installer_data:
            raise Installer.DoesNotExist
        return json.dumps(installer_data, indent=2)


class BaseInstaller(models.Model):
    """Base class for Installer-like classes."""
    class Meta:
        abstract = True

    @property
    def raw_script(self):
        return self.as_dict(with_metadata=False)

    @property
    def game_slug(self):
        return self.game.slug

    def as_dict(self, with_metadata=True):
        yaml_content = yaml.safe_load(self.content) or {}

        # Allow pasting raw install scripts (which are served as lists)
        if isinstance(yaml_content, list):
            yaml_content = yaml_content[0]

        # If yaml content evaluates to a string return an empty dict
        if isinstance(yaml_content, six.string_types):
            return {}

        # Do not add metadata if the clean argument has been passed
        if with_metadata:
            yaml_content['game_slug'] = self.game.slug
            yaml_content['version'] = self.version
            yaml_content['description'] = self.description
            yaml_content['notes'] = self.notes
            yaml_content['name'] = self.game.name
            yaml_content['year'] = self.game.year
            yaml_content['steamid'] = self.game.steamid
            yaml_content['gogslug'] = self.game.gogslug
            yaml_content['humblestoreid'] = self.game.humblestoreid
            try:
                yaml_content['runner'] = self.runner.slug
            except ObjectDoesNotExist:
                yaml_content['runner'] = ''
            # Set slug to both slug and installer_slug for backward compatibility
            # reasons with the client. Remove installer_slug sometime in the future
            yaml_content['slug'] = self.slug
            yaml_content['installer_slug'] = self.slug
        return yaml_content

    def as_yaml(self):
        return yaml.safe_dump(self.as_dict(), default_flow_style=False)

    def as_json(self):
        return json.dumps(self.as_dict(), indent=2)

    def as_cleaned_yaml(self):
        """Return the YAML installer without the metadata"""
        return yaml.safe_dump(self.as_dict(with_metadata=False), default_flow_style=False)

    def as_cleaned_json(self):
        """Return the JSON installer without the metadata"""
        return json.dumps(self.as_dict(with_metadata=False), indent=2)

    def build_slug(self, version):
        slug = "%s-%s" % (slugify(self.game.name)[:29],
                          slugify(version)[:20])
        return get_auto_increment_slug(self.__class__, self, slug)


@reversion.register()
class Installer(BaseInstaller):
    """Game installer model"""

    RATINGS = {
        'platinum': 'Platinum: installs and runs flawlessly',
        'gold': 'Gold: works flawlessly with some minor tweaking',
        'silver': ('Silver: works excellently for "normal" use but some '
                   'features may be broken'),
        'bronze': 'Bronze: works: but has some issues: even for normal use',
        'garbage': 'Garbage: game is not playable'
    }

    game = models.ForeignKey(Game, related_name='installers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    runner = models.ForeignKey('runners.Runner')

    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=32)
    description = models.CharField(max_length=512, blank=True, null=True)
    notes = models.TextField(blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    draft = models.BooleanField(default=False)
    rating = models.CharField(max_length=24, choices=RATINGS.items(), blank=True)
    objects = InstallerManager()

    def __unicode__(self):
        return self.slug

    def set_default_installer(self):
        if self.game and self.game.steam_support():
            installer_data = {'game': {'appid': self.game.steamid}}
            self.version = 'Steam'
        else:
            installer_data = DEFAULT_INSTALLER
        self.content = yaml.safe_dump(installer_data, default_flow_style=False)

    @property
    def revisions(self):
        return [
            InstallerRevision(version)
            for version
            in Version.objects.filter(
                content_type__model='installer', object_id=self.id
            )
        ]

    def save(self, force_insert=True, using=None):
        self.slug = self.build_slug(self.version)
        return super(Installer, self).save()


class InstallerIssue(models.Model):
    """Model to store problems about installers or update requests"""
    installer = models.ForeignKey(Installer)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    submitted_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    def __unicode__(self):
        return "Issue for {}".format(self.installer.slug)

    def get_absolute_url(self):
        return reverse('admin:games_installerissue_change', args=(self.id, ))


class GameLibrary(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    games = models.ManyToManyField(Game)

    # pylint: disable=W0232, R0903
    class Meta:
        verbose_name_plural = "game libraries"

    def __unicode__(self):
        return u"%s's library" % self.user.username


class Featured(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    image = models.ImageField(upload_to='featured', max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # pylint: disable=W0232, R0903
    class Meta:
        verbose_name = "Featured content"

    def __unicode__(self):
        return "[%s] %s" % (self.content_type, str(self.content_object), )


class GameSubmission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    game = models.ForeignKey(Game)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True)

    class Meta:
        verbose_name = "User submitted game"

    def __unicode__(self):
        return u"{0} submitted {1} on {2}".format(self.user, self.game,
                                                  self.created_at)

    def accept(self):
        self.accepted_at = datetime.datetime.now()
        self.save()
        messages.send_game_accepted(self.user, self.game)


class GameLink(models.Model):
    WEBSITE_CHOICES = (
        ('wikipedia', 'Wikipedia'),
        ('pcgamingwiki', 'PCGamingWiki'),
        ('mobygames', 'MobyGames'),
        ('winehq', 'WineHQ AppDB'),
        ('lemonamiga', 'Lemon Amiga'),
        ('github', 'Github'),
    )
    game = models.ForeignKey(Game, related_name='links')
    website = models.CharField(blank=True, choices=WEBSITE_CHOICES, max_length=32)
    url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        """Additional configuration for model"""
        verbose_name = "External link"
        ordering = ['website']


class InstallerRevision(BaseInstaller):
    def __init__(self, version):
        super(InstallerRevision, self).__init__()
        self._version = version
        self.id = version.pk
        installer_data = self.get_installer_data()
        self.game = Game.objects.get(pk=installer_data['game'])

        self.name = self.game.name

        self.comment = self._version.revision.comment
        self.user = self._version.revision.user
        self.created_at = self._version.revision.date_created
        self.draft = installer_data['draft']
        self.published = installer_data['published']
        self.rating = installer_data['rating']

        self.script = installer_data['script']
        self.content = installer_data['content']

        self.user = self.user
        self.runner = Runner.objects.get(pk=installer_data['runner'])
        self.slug = installer_data['slug']
        self.version = installer_data['version']
        self.description = installer_data['description']
        self.notes = installer_data['notes']

        self.installer_id = self._version.object_id

    def __unicode__(self):
        return self.comment

    def get_installer_data(self):
        installer_data = json.loads(self._version.serialized_data)[0]['fields']
        try:
            installer_data['script'] = yaml.safe_load(installer_data['content'])
        except yaml.scanner.ScannerError:
            installer_data['script'] = ['This installer is fucked up.']
        installer_data['id'] = self.id
        return installer_data

    def delete(self, using=None, keep_parents=False):
        self._version.delete()

    def accept(self):
        self._version.revert()
        installer = Installer.objects.get(pk=self.installer_id)
        installer.published = True
        installer.draft = False
        installer.save()
        self.delete()


class AutoInstaller(BaseInstaller):
    published = True
    draft = False
    auto = True
    description = ""
    notes = ""
    user = None
    rating = None
    created_at = None
    updated_at = None

    def __init__(self, game, platform):
        super(AutoInstaller, self).__init__()
        self.game = game
        if platform not in game.platforms.all():
            raise ObjectDoesNotExist
        self.script = platform.default_installer
        self.content = json.dumps(self.script)
        self.name = game.name
        self.version = platform.name
        self.slug = "-".join((game.slug[:30], platform.slug[:20]))
        self.platform = platform.slug
        self.runner = Runner.objects.get(slug=self.script.pop('runner'))

    @property
    def raw_script(self):
        return self.script
