"""Models for main lutris app"""
# pylint: disable=E1002
import yaml
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from bitfield import BitField

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


class Platform(models.Model):
    """Gaming platform"""
    name = models.CharField(_('Name'), max_length=127)
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='platforms/icons', blank=True)

    # pylint: disable=W0232, R0903
    class Meta:
        ordering = ('name', )

    def __unicode__(self):
        return "%s" % self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super(Platform, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', )


class Company(models.Model):
    """Gaming company"""
    name = models.CharField(_('Name'), max_length=127)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='companies/logos', blank=True)
    website = models.CharField(max_length=128, blank=True)

    # pylint: disable=W0232, R0903
    class Meta:
        """Additional configuration for model"""
        verbose_name_plural = "companies"
        ordering = ['name']

    def get_absolute_url(self):
        return reverse("games_by_company", args=(self.slug, ))

    def __unicode__(self):
        return "%s" % self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super(Company, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', 'slug__icontains')


class Runner(models.Model):
    '''Model definition for the runners.'''
    name = models.CharField(_("Name"), max_length=127)
    slug = models.SlugField(unique=True)
    website = models.CharField(_("Website"), max_length=127, blank=True)
    icon = models.ImageField(upload_to='runners/icons', blank=True)
    platforms = models.ManyToManyField(Platform)

    # pylint: disable=W0232, R0903
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Runner, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', )


class Genre(models.Model):
    """Gaming genre"""
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    # pylint: disable=W0232, R0903
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', )


class GameManager(models.Manager):
    def published(self):
        return self.get_query_set().filter(is_public=True,
                                           installer__isnull=False)


class Game(models.Model):
    """Game model"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=False)
    year = models.IntegerField(null=True, blank=True)
    platforms = models.ManyToManyField(Platform, null=True, blank=True)
    genres = models.ManyToManyField(Genre, null=True, blank=True)
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
    created = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)
    steamid = models.PositiveIntegerField(null=True, blank=True)
    flags = BitField(flags=(
        'open_source',
        'open_engine',
        'freeware',
    ))

    objects = GameManager()

    # pylint: disable=W0232, R0903
    class Meta:
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
        return self.installer_set.count() > 0

    def get_absolute_url(self):
        """Return the absolute url for a game"""
        return "/games/%s/" % self.slug

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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:50]
        self.download_steam_capsule()
        return super(Game, self).save(*args, **kwargs)


class Screenshot(models.Model):
    """Screenshots for games"""
    game = models.ForeignKey(Game)
    image = models.ImageField(upload_to="games/screenshots")
    uploaded_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    description = models.CharField(max_length=256, null=True, blank=True)
    published = models.BooleanField(default=False)

    objects = managers.ScreenshotManager()

    def __unicode__(self):
        desc = self.description if self.description else self.game.name
        return "%s: %s (uploaded by %s)" % (self.game, desc, self.uploaded_by)


class InstallerManager(models.Manager):
    def published(self, user=None):
        if user:
            return self.get_query_set().filter(models.Q(published=True)
                                               | models.Q(user=user))
        else:
            return self.get_query_set().filter(published=True)

    def fuzzy_get(self, slug):
        try:
            installer = self.get_query_set().get(slug=slug)
            return installer
        except ObjectDoesNotExist:
            installers = self.get_query_set().filter(game__slug=slug,
                                                     published=True)
            if not installers:
                raise
            else:
                return installers[0]


class Installer(models.Model):
    """Game installer model"""
    game = models.ForeignKey(Game)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    runner = models.ForeignKey(Runner)

    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=32)
    description = models.CharField(max_length=512, blank=True, null=True)
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
            self.version = 'steam'
        else:
            installer_data = DEFAULT_INSTALLER
        yaml_data = yaml.safe_dump(installer_data, default_flow_style=False)
        self.content = yaml_data

    def save(self, *args, **kwargs):
        self.slug = "%s-%s" % (
            slugify(self.game.name)[:30], slugify(self.version)[:20]
        )
        return super(Installer, self).save(*args, **kwargs)


class GameLibrary(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    games = models.ManyToManyField(Game)

    # pylint: disable=W0232, R0903
    class Meta:
        verbose_name_plural = "game libraries"

    def __unicode__(self):
        return "%s's library" % self.user.username


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
