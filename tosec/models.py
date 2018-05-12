# pylint: disable=R0903
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    category = models.CharField(max_length=256)
    version = models.CharField(max_length=32)
    author = models.CharField(max_length=128)
    section = models.CharField(max_length=12, default='TOSEC')

    def __str__(self):
        return self.name

    class Meta(object):
        verbose_name_plural = 'Categories'
        ordering = ('name', )


class Game(models.Model):
    category = models.ForeignKey(Category)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(object):
        ordering = ('category', 'name')


class Rom(models.Model):
    game = models.ForeignKey(Game, related_name='roms')
    name = models.CharField(max_length=255)
    size = models.IntegerField()
    crc = models.CharField(max_length=16)
    md5 = models.CharField(max_length=32)
    sha1 = models.CharField(max_length=64)

    def __str__(self):
        return self.name
