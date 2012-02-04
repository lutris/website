import os

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext as _


def generate_installer_name(instance, filename):
    return os.path.join('installers', instance.slug + ".yml")


class Platform(models.Model):
    name = models.CharField(_('Name'), max_length=127)
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='platform_icons', blank=True)

    def __unicode__(self):
        return "%s" % self.name


class Company(models.Model):
    name = models.CharField(_('Name'), max_length=127)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='company_logos', blank=True)
    website = models.CharField(max_length=128, blank=True)

    class Meta:
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
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.name


class Game(models.Model):
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
    icon = models.ImageField(upload_to='game_icons', blank=True)
    cover = models.ImageField(upload_to='game_covers', blank=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "/games/%s" % self.slug


class Installer(models.Model):
    game = models.ForeignKey(Game)
    slug = models.SlugField(unique=True)
    user = models.ForeignKey(User)
    version = models.CharField(max_length=32)
    install_file = models.FileField(upload_to=generate_installer_name)
