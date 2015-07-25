"""Models for main lutris app"""
# pylint: disable=E1002, E0202
import yaml
import json
import datetime
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q, Count
from django.conf import settings
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from bitfield import BitField

from common.util import get_auto_increment_slug
from platforms.models import Platform
from games import managers
from games.util import steam

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
    name = models.CharField(_('Name'), max_length=127)
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

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super(Company, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', 'slug__icontains')


class Genre(models.Model):
    """Gaming genre"""
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    # pylint: disable=W0232, R0903
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Genre, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', )


class GameManager(models.Manager):
    def published(self):
        return self.get_queryset().filter(is_public=True)

    def with_installer(self):
        return (
            self.get_queryset()
            .filter(is_public=True)
            .filter(
                Q(installer__published=True)
                # Disable auto-installer stuff until switch to DRF
                # | Q(platforms__default_installer__isnull=False)
            )
            .order_by('name')
            .annotate(installer_count=Count('installer'))
            .annotate(default_installer_count=Count('platforms'))
        )


class Game(models.Model):
    """Game model"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=False)
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
    is_public = models.BooleanField("Published on website", default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    steamid = models.PositiveIntegerField(null=True, blank=True)
    flags = BitField(flags=(
        ('fully_libre', 'Fully libre'),
        ('open_engine', 'Open engine only'),
        ('free', 'Free'),
        ('freetoplay', 'Free-to-play'),
        ('pwyw', 'Pay what you want'),
    ))

    objects = GameManager()

    # pylint: disable=W0232, R0903
    class Meta(object):
        ordering = ['name']
        permissions = (
            ('can_publish_game', "Can make the game visible"),
        )

    def __unicode__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains",)

    def has_installer(self):
        return self.installer_set.count() > 0 \
            or bool(self.get_default_installers())

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
        else:
            return True

    def get_default_installers(self):
        installers = []
        for platform in self.platforms.all():
            if platform.default_installer:
                installer = platform.default_installer
                installer['name'] = self.name
                installer['version'] = platform.slug
                installer['installer_slug'] = "-".join((self.slug[:30],
                                                        platform.slug[:20]))
                installer['platform'] = platform.slug
                installer['description'] = platform.name + " version"
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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:50]
        self.download_steam_capsule()
        self.check_for_submission()
        return super(Game, self).save(*args, **kwargs)


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
    def published(self, user=None, is_staff=False):
        if is_staff:
            return self.get_queryset()
        elif user:
            return self.get_queryset().filter(models.Q(published=True)
                                              | models.Q(user=user))
        else:
            return self.get_queryset().filter(published=True)

    def fuzzy_get(self, slug):
        """Return either the installer that matches exactly 'slug' or the
        installers with game matching slug.
        Installers are always returned in a list.
        """
        try:
            installer = self.get_queryset().get(slug=slug)
            return [installer]
        except ObjectDoesNotExist:
            installers = self.get_queryset().filter(game__slug=slug,
                                                    published=True)
            if not installers:
                raise
            else:
                return installers

    def get_json(self, slug):
        try:
            installers = self.fuzzy_get(slug)
        except ObjectDoesNotExist:
            installer_data = []
        else:
            installer_data = [installer.as_dict() for installer in installers]
        try:
            game = Game.objects.get(slug=slug)
            installer_data += game.get_default_installers()
        except ObjectDoesNotExist:
            pass
        if not installer_data:
            raise Installer.DoesNotExist
        return json.dumps(installer_data)


class Installer(models.Model):
    """Game installer model"""
    from runners.models import Runner
    game = models.ForeignKey(Game)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    runner = models.ForeignKey(Runner)

    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=32)
    description = models.CharField(max_length=512, blank=True, null=True)
    notes = models.CharField(max_length=512, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
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

    def as_dict(self):
        from runners.models import Runner
        yaml_content = yaml.safe_load(self.content) or {}

        # If yaml content evaluates to a string return an empty dict
        if isinstance(yaml_content, basestring):
            return {}
        yaml_content['game_slug'] = self.game.slug
        yaml_content['version'] = self.version
        yaml_content['description'] = self.description
        yaml_content['notes'] = self.notes
        yaml_content['name'] = self.game.name
        yaml_content['year'] = self.game.year
        yaml_content['steamid'] = self.game.steamid
        try:
            yaml_content['runner'] = self.runner.slug
        except Runner.DoesNotExist:
            yaml_content['runner'] = ''
        yaml_content['installer_slug'] = self.slug
        return yaml_content

    def as_yaml(self):
        return yaml.safe_dump(self.as_dict())

    def as_json(self):
        return json.dumps(self.as_dict())

    def build_slug(self, version):
        slug = "%s-%s" % (slugify(self.game.name)[:29],
                          slugify(version)[:20])
        return get_auto_increment_slug(self.__class__, self, slug)

    def save(self, *args, **kwargs):
        self.slug = self.build_slug(self.version)
        return super(Installer, self).save(*args, **kwargs)


class InstallerIssue(models.Model):
    """Model to store problems about installers or update requests"""
    installer = models.ForeignKey(Installer)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    submitted_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    def __unicode__(self):
        return "Issue for {}".format(self.installer.slug)


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
    content_object = generic.GenericForeignKey('content_type', 'object_id')
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
        subject = u"{} Your game submission for '{}' as been accepted!".format(
            settings.EMAIL_SUBJECT_PREFIX,
            self.game.name
        )
        body = u"""
Hello {0}!

Your submission for {1} has been reviewed by a moderator and approved!

The game's page is available at https://lutris.net{2}
You can submit an installer script for it if you haven't done so already. The
scripting details are explained on the installer submission page, you can have
a look at other scripts to see how they are written. If you get confused or
have any questions about the scripting process, please drop us a line at
admin@lutris.net or on IRC: #lutris on Freenode.

Have a great day!

The Lutris team
        """.format(
            self.user.username,
            self.game.name,
            self.game.get_absolute_url()
        )
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [self.user.email])
