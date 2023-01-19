"""TOSEC models"""
from django.db import models


class TosecCategory(models.Model):
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    category = models.CharField(max_length=256)
    version = models.CharField(max_length=32)
    author = models.TextField()
    section = models.CharField(max_length=12, default='TOSEC')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('name', )


class TosecGame(models.Model):
    category = models.ForeignKey(TosecCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    @property
    def collection(self):
        return self.category.category

    class Meta:
        ordering = ('category', 'name')


class TosecRom(models.Model):
    game = models.ForeignKey(TosecGame, related_name='roms', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    size = models.BigIntegerField()
    crc = models.CharField(max_length=16)
    md5 = models.CharField(max_length=32)
    sha1 = models.CharField(max_length=64)

    def __str__(self):
        return self.name
