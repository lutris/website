from django.urls import reverse
from django.db import models
from games.models import Game


class Bundle(models.Model):
    games = models.ManyToManyField(Game, related_name="bundles")
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('bundle_detail', kwargs={'slug': self.slug})
