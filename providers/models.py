"""Models for game providers"""
# pylint: disable=too-few-public-methods
import logging

from django.db import models
from django.contrib.postgres.fields import JSONField


LOGGER = logging.getLogger(__name__)

class Provider(models.Model):
    """An entity that provides games like a Store (GOG, Humble Bundle) or a
    database (TOSEC, MobyGames).
    """
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField()

    def __str__(self):
        return str(self.name)


class ProviderResource(models.Model):
    """Base model with functionality to import from IGDB API"""
    class Meta:
        """Set as abstract model"""
        abstract = True

    @classmethod
    def create_from_igdb_api(cls, provider, api_payload):
        """Create an instance from an IGDB payload"""
        resource, _created = cls.objects.get_or_create(
            provider=provider,
            slug=api_payload["slug"]
        )
        resource.name = api_payload["name"]
        resource.metadata = api_payload
        resource.save()
        LOGGER.info("Created %s", resource["name"])


class ProviderGame(ProviderResource):
    """Games from providers, along with any provider specific data."""
    name = models.CharField(max_length=255, blank=True)
    slug = models.CharField(max_length=255)
    provider = models.ForeignKey(
        Provider,
        related_name="games",
        on_delete=models.PROTECT,
    )
    updated_at = models.DateTimeField(auto_now=True)
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

class ProviderGenre(ProviderResource):
    """Genres given by providers"""
    name = models.CharField(max_length=128)
    slug = models.SlugField()
    provider = models.ForeignKey(
        Provider,
        related_name="genres",
        on_delete=models.PROTECT
    )
    metadata = JSONField(null=True)

class ProviderPlatform(ProviderResource):
    """Platforms given by providers"""
    name = models.CharField(max_length=128)
    slug = models.SlugField()
    provider = models.ForeignKey(
        Provider,
        related_name="platforms",
        on_delete=models.PROTECT
    )
    metadata = JSONField(null=True)


class ProviderCover(ProviderResource):
    """Platforms given by providers"""
    game = models.IntegerField(null=True)
    image_id = models.SlugField()
    provider = models.ForeignKey(
        Provider,
        related_name="covers",
        on_delete=models.PROTECT
    )
    metadata = JSONField(null=True)

    @classmethod
    def create_from_igdb_api(cls, provider, api_payload):
        """Create an instance from an IGDB payload"""
        resource, _created = cls.objects.get_or_create(
            provider=provider,
            image_id=api_payload["image_id"]
        )
        resource.game = api_payload["game"]
        resource.metadata = api_payload
        resource.save()
        LOGGER.info("Created cover %s", api_payload["image_id"])
