"""Provider tasks"""
import time
import logging

from django.conf import settings

from celery import task
from providers.igdb import IGDBClient
from providers.gog import cache_gog_games
from providers.models import Provider, ProviderGame, ProviderGenre, ProviderPlatform

LOGGER = logging.getLogger(__name__)

@task
def refresh_cache():
    """Reload the local GOG cache"""
    cache_gog_games()


@task
def load_igdb_games():
    """Load all games from IGDB"""
    client = IGDBClient(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    client.get_authentication_token()
    games = True
    page = 1
    provider, _created = Provider.objects.get_or_create(name="igdb")
    while games:
        LOGGER.info("Getting page %s of IGDB API", page)
        response = client.get_games(page=page)
        games = response.json()
        for game in games:
            provider_game, _created = ProviderGame.objects.get_or_create(
                provider=provider,
                slug=game["id"]
            )
            provider_game.name = game["name"]
            provider_game.metadata = game
            provider_game.save()
            LOGGER.info("Created %s", game["name"])
        page += 1


@task
def load_igdb_genres():
    client = IGDBClient(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    client.get_authentication_token()
    client.page_size = 10
    genres = True
    page = 1
    provider, _created = Provider.objects.get_or_create(name="igdb")
    while genres:
        LOGGER.info("Getting page %s of IGDB API", page)
        response = client.get_genres(page=page)
        genres = response.json()
        for genre in genres:
            provider_genre, _created = ProviderGenre.objects.get_or_create(
                provider=provider,
                slug=genre["id"]
            )
            provider_genre.name = genre["name"]
            provider_genre.metadata = genre
            provider_genre.save()
            LOGGER.info("Genre created %s", genre["name"])
        page += 1


@task
def load_igdb_platforms():
    client = IGDBClient(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    client.get_authentication_token()
    client.page_size = 10
    platforms = True
    page = 1
    provider, _created = Provider.objects.get_or_create(name="igdb")
    while platforms:
        LOGGER.info("Getting platforms page %s of IGDB API", page)
        response = client.get_platforms(page=page)
        platforms = response.json()
        for platform in platforms:
            provider_platform, _created = ProviderPlatform.objects.get_or_create(
                provider=provider,
                slug=platform["id"]
            )
            provider_platform.name = platform["name"]
            provider_platform.metadata = platform
            provider_platform.save()
            LOGGER.info("Platform created %s", platform["name"])
        page += 1