"""Sync Steam games"""
import requests

from celery import task
from celery.utils.log import get_task_logger

from providers import models


LOGGER = get_task_logger(__name__)


API_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/?"


@task
def load_steam_games():
    """Query the Steam API and load every game as a ProviderGame"""
    provider = models.Provider.objects.get(name="steam")
    response = requests.get(API_URL)
    game_list = response.json()["applist"]["apps"]
    stats = {
        "created": 0,
        "updated": 0
    }
    for game in game_list:
        provider_game, created = models.ProviderGame.objects.get_or_create(
            slug=game["appid"],
            provider=provider
        )
        provider_game.name = game["name"]
        provider_game.save()
        if created:
            stats["created"] += 1
            LOGGER.info("Created %s (%s)", game["name"], game["appid"])
        else:
            stats["updated"] += 1
    LOGGER.info("Created: %s, Updated: %s", stats["created"], stats["updated"])
    return stats
