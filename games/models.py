"""Models for main lutris app"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.contrib.sites.models import Site

from mithril.models import Whitelist


class SiteACL(models.Model):
    site = models.OneToOneField(Site)
    whitelist = models.ForeignKey(Whitelist, related_name='site_acl')


class News(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    publish_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-publish_date']
        verbose_name_plural = "news"

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return '/news/%s/' % self.slug

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        return super(News, self).save(*args, **kwargs)


class Platform(models.Model):
    """Gaming platform"""
    name = models.CharField(_('Name'), max_length=127)
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='platforms/icons', blank=True)

    def __unicode__(self):
        return "%s" % self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super(Platform, self).save(*args, **kwargs)


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

    def __unicode__(self):
        return "%s" % self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super(Company, self).save(*args, **kwargs)


class Runner(models.Model):
    '''Model definition for the runners.'''
    name = models.CharField(_("Name"), max_length=127)
    slug = models.SlugField(unique=True)
    website = models.CharField(_("Website"), max_length=127)
    icon = models.ImageField(upload_to='runners/icons', blank=True)
    platforms = models.ManyToManyField(Platform)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super(Runner, self).save(*args, **kwargs)


class Genre(models.Model):
    """Gaming genre"""
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Game(models.Model):
    """Game model"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    platforms = models.ManyToManyField(Platform, null=True)
    year = models.IntegerField(null=True, blank=True)
    genres = models.ManyToManyField(Genre, null=True)
    publisher = models.ForeignKey(
        Company, related_name='published_game', null=True, blank=True
    )
    developer = models.ForeignKey(
        Company, related_name='developed_game', null=True, blank=True
    )
    website = models.CharField(max_length=200, blank=True)
    icon = models.ImageField(upload_to='games/icons', blank=True)
    cover = models.ImageField(upload_to='games/covers', blank=True)
    title_logo = models.ImageField(upload_to='games/banners', blank=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        """Return the absolute url for a game"""
        return "/games/%s/" % self.slug


class Screenshot(models.Model):
    """Screenshots for games"""
    game = models.ForeignKey(Game)
    image = models.ImageField(upload_to="games/screenshots")
    uploaded_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(User)
    description = models.CharField(max_length=256, null=True, blank=True)

    def __unicode__(self):
        desc = self.description if self.description else self.game.name
        return "%s uploaded by %s" % (desc, self.uploaded_by)


class Installer(models.Model):
    """Game installer model"""
    game = models.ForeignKey(Game)
    user = models.ForeignKey(User)
    runner = models.ForeignKey(Runner)

    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=32)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now=True, null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.game.name + "-" + self.version)
        return super(Installer, self).save(*args, **kwargs)
