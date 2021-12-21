"""Models for game providers"""
# pylint: disable=too-few-public-methods
from django.db import models
from django.contrib.postgres.fields import JSONField


class Provider(models.Model):
    """An entity that provides games like a Store (GOG, Humble Bundle) or a
    database (TOSEC, MobyGames).
    """
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField()

    def __str__(self):
        return str(self.name)


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

    class Meta:
        """Model configuration"""
        unique_together = [["slug", "provider"]]

    def __str__(self):
        return f"[{self.provider}] {self.name or self.slug}"

    @staticmethod
    def autocomplete_search_fields():
        """Autocomplete fields used in the Django admin"""
        return ("name__icontains", "slug__icontains")


class ProviderGenre(models.Model):
    """Genres given by providers"""
    name = models.CharField(max_length=128)
    slug = models.SlugField()
    provider = models.ForeignKey(
        Provider,
        related_name="genres",
        on_delete=models.PROTECT
    )
    metadata = JSONField(null=True)

class ProviderPlatform(models.Model):
    """Platforms given by providers"""
    name = models.CharField(max_length=128)
    slug = models.SlugField()
    provider = models.ForeignKey(
        Provider,
        related_name="platforms",
        on_delete=models.PROTECT
    )
    metadata = JSONField(null=True)
