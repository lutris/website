from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
import os

def generate_installer_name(instance, filename):
    return os.path.join('installers', instance.slug + ".yml")

class Platform(models.Model):
    name = models.CharField(_('Name'), max_length=127)
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='platform_icons', blank=True)

    def __unicode__(self):
        return self.name

class Runner(models.Model):
    name = models.CharField(_("Name"), max_length=127)
    slug = models.SlugField(unique=True)
    website = models.CharField(_("Website"), max_length=127)
    icon = models.ImageField(upload_to='runner_icons', blank=True)

    def __unicode__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

class Game(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    runner = models.ForeignKey(Runner)
    publisher = models.CharField(max_length=200)
    developer = models.CharField(max_length=200)
    website = models.CharField(max_length=200)
    installer = models.FileField(upload_to=generate_installer_name, blank=True, null=True)
    genre = models.ForeignKey(Genre)
    icon = models.ImageField(upload_to='game_icons', blank=True)
    cover = models.ImageField(upload_to='game_covers', blank=True)



    def __unicode__(self):
        return self.name


