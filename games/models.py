from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
import os

def generate_installer_name(instance, filename):
    return os.path.join('installers', instance.slug + ".yml")

class Runner(models.Model):
    name = models.CharField(_("Name"), max_length = 200)
    website = models.CharField(_("Website"), max_length = 200)

    def __unicode__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length = 50)

    def __unicode__(self):
        return self.name

class Game(models.Model):
    name = models.CharField(max_length = 200)
    slug = models.SlugField(unique = True)
    runner = models.ForeignKey(Runner)
    publisher = models.CharField(max_length = 200)
    developer = models.CharField(max_length = 200)
    website = models.CharField(max_length = 200)
    installer = models.FileField(upload_to = generate_installer_name, blank = True, null = True)
    genre = models.ForeignKey(Genre)

    def __unicode__(self):
        return self.name


