"""Provider tasks"""
from datetime import datetime

from django.conf import settings

from celery import task
from celery.utils.log import get_task_logger
from games.models import Game
from providers.igdb import IGDBClient
from providers.gog import cache_gog_games
from providers.models import Provider, ProviderGame, ProviderGenre, ProviderPlatform, ProviderCover

LOGGER = get_task_logger(__name__)

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


@task
def match_igdb_games():
    """Create or update Lutris games from IGDB games"""
    igdb_games = ProviderGame.objects.filter(provider__name="igdb")
    for igdb_game in igdb_games:
        igdb_slug = igdb_game.metadata["slug"]

        try:
            lutris_game = Game.objects.get(slug=igdb_slug)
            LOGGER.info("Updating Lutris game %s", igdb_game.name)
        except Game.DoesNotExist:
            LOGGER.info("Creating Lutris game %s", igdb_game.name)
            lutris_game = Game.objects.create(
                name=igdb_game.name,
                slug=igdb_slug,
            )
        if not lutris_game.year and igdb_game.metadata.get("first_release_date"):
            lutris_game.year = datetime.fromtimestamp(igdb_game.metadata["first_release_date"]).year

        if not lutris_game.description and igdb_game.metadata.get("summary"):
            lutris_game.description = igdb_game.metadata.get("summary")
        lutris_game.provider_games.add(igdb_game)
        lutris_game.is_public = True
        lutris_game.save()
