"""Provider tasks"""
import logging
from django.conf import settings

from celery import task
from providers.igdb import IGDBClient
from providers.gog import cache_gog_games
from providers.models import Provider, ProviderGame

LOGGER = logging.getLogger(__name__)

@task
def refresh_cache():
    """Reload the local GOG cache"""
    cache_gog_games()


@task
def load_idgb_games():
    """Load all games from IGDB"""
    client = IGDBClient(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    client.get_authentication_token()
    games = True
    page = 1
    provider, _created = Provider.objects.get_or_create(name="IDGB")
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
