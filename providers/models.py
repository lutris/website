"""Models for game providers"""
from django.db import models
from django.contrib.postgres.fields import JSONField


class Provider(models.Model):
    """An entity that provides games like a Store (GOG, Humble Bundle) or a
    database (TOSEC, MobyGames).
    """
    name = models.CharField(max_length=255)
    website = models.URLField()

    def __str__(self):
        return self.name


class ProviderGame(models.Model):
    """Games from providers, along with any provider specific data."""
    name = models.CharField(max_length=255, blank=True)
    slug = models.CharField(max_length=255)
    provider = models.ForeignKey(
        Provider,
        related_name="games",
        on_delete=models.PROTECT,
    )
    metadata = JSONField(null=True)

    def __str__(self):
        return "[%s] %s" % (self.provider, self.name or self.slug)

    @staticmethod
    def autocomplete_search_fields():
        """Autocomplete fields used in the Django admin"""
        return ("name__icontains", "slug__icontains")
