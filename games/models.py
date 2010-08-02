from django.db import models

class Runner(models.Model):
    name = models.CharField(_("Name"), max_length = 200)
    website = models.CharField(_("Website"), max_length = 200)

class Genre(models.Model):
    name = models.CharField(max_length = 50)

class Game(models.Model):
    name = models.CharField(max_length = 200)
    runner = models.ForeignKey(Runner)
    publisher = models.CharField(max_length = 200)
    developer = models.CharField(max_length = 200)
    website = models.CharField(max_length = 200)
    installer = models.FileField()
    genre = models.ForeignKey(Genre)
