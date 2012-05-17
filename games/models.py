"""Models for main lutris app"""
import os

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


def generate_installer_name(instance):
    """Return the path to installer file"""
    return os.path.join('installers', instance.slug + ".yml")


class Platform(models.Model):
    """Gaming platform"""
    name = models.CharField(_('Name'), max_length=127)
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='platforms/icons', blank=True)

    def __unicode__(self):
        return "%s" % self.name


class Company(models.Model):
    """Gaming company"""
    name = models.CharField(_('Name'), max_length=127)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='company_logos', blank=True)
    website = models.CharField(max_length=128, blank=True)

    # pylint: disable=W0232, R0903
    class Meta:
        """Additional configuration for model"""
        verbose_name_plural = "companies"

    def __unicode__(self):
        return "%s" % self.name


class Runner(models.Model):
    '''Model definition for the runners.'''
    name = models.CharField(_("Name"), max_length=127)
    slug = models.SlugField(unique=True)
    website = models.CharField(_("Website"), max_length=127)
    icon = models.ImageField(upload_to='runner_icons', blank=True)

    def __unicode__(self):
        return self.name


class RunnerPlatform(models.Model):
    '''Model to associate runners and platforms.'''
    runner = models.ForeignKey(Runner)
    platform = models.ForeignKey(Platform)
    notes = models.TextField(blank=True)


class Genre(models.Model):
    """Gaming genre"""
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.name


class Game(models.Model):
    """Game model"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    runner = models.ForeignKey(Runner, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    genre = models.ForeignKey(Genre, null=True, blank=True)
    publisher = models.ForeignKey(Company,
            related_name='published_game',
            null=True, blank=True)
    developer = models.ForeignKey(Company,
            related_name='developed_game',
            null=True, blank=True)
    website = models.CharField(max_length=200, blank=True)
    icon = models.ImageField(upload_to='games/icons', blank=True)
    cover = models.ImageField(upload_to='games/covers', blank=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        """Return the absolute url for a game"""
        return "/games/%s" % self.slug


class Screenshot(models.Model):
    """Screenshots for games"""
    game = models.ForeignKey(Game)
    image = models.ImageField(upload_to="games/screenshots")
    uploaded_at = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=256, null=True, blank=True)

    def __unicode__(self):
        return "Screenshot for %s uploaded at %s" % (self.game.name,
                                                     self.uploaded_at)


class Installer(models.Model):
    """Game installer model"""
    game = models.ForeignKey(Game)
    slug = models.SlugField(unique=True)
    user = models.ForeignKey(User)
    version = models.CharField(max_length=32)
    install_file = models.FileField(upload_to=generate_installer_name)
