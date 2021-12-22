"""Provider tasks"""
import logging

from django.conf import settings

from celery import task
from providers.igdb import IGDBClient
from providers.gog import cache_gog_games
from providers.models import Provider, ProviderGame, ProviderGenre, ProviderPlatform, ProviderCover

LOGGER = logging.getLogger(__name__)

@task
def refresh_cache():
    """Reload the local GOG cache"""
    cache_gog_games()


def _igdb_loader(resource_name, model):
    """Generic function to load a collection from IGDB to database"""
    client = IGDBClient(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    client.get_authentication_token()
    if resource_name not in ("games", "covers"):
        client.page_size = 10  # Most endpoints don't seem to support large page sizes
    resources = True
    page = 1
    provider, _created = Provider.objects.get_or_create(name="igdb")
    while resources:
        LOGGER.info("Getting page %s of IGDB API", page)
        response = client.get_resources(f"{resource_name}/", page=page)
        resources = response.json()
        for api_payload in resources:
            model.create_from_igdb_api(provider, api_payload)
        page += 1


@task
def load_igdb_games():
    """Load all games from IGDB"""
    _igdb_loader("games", ProviderGame)


@task
def load_igdb_genres():
    """Load all genres from IGDB"""
    _igdb_loader("genres", ProviderGenre)


@task
def load_igdb_platforms():
    """Load all platforms from IGDB"""
    _igdb_loader("platforms", ProviderPlatform)


@task
def load_igdb_covers():
    """Load all covers from IGDB"""
    _igdb_loader("covers", ProviderCover)
