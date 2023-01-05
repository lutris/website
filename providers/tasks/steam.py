"""Sync Steam games"""
import requests

from celery import task
from celery.utils.log import get_task_logger

from providers import models
from games.models import Game
from common.models import save_action_log

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
        provider_game.internal_id = game["appid"]
        provider_game.save()
        if created:
            stats["created"] += 1
            LOGGER.info("Created %s (%s)", game["name"], game["appid"])
        else:
            stats["updated"] += 1
    LOGGER.info("Created: %s, Updated: %s", stats["created"], stats["updated"])
    save_action_log("load_steam_games", stats)
    return stats


@task
def match_steam_games():
    """Match Steam provider games with those imported from user libraries"""
    stats = {
        "matched": 0,
        "same_name_exists": 0,
        "ambiguous_name": 0,
    }
    for steam_game in models.ProviderGame.objects.filter(provider__name="steam"):
        existing_games = Game.objects.filter(steamid=steam_game.slug)
        for lutris_game in existing_games:
            lutris_game.provider_games.add(steam_game)
            stats["matched"] += 1
            if not lutris_game.is_public:
                lutris_game.is_public = True
                lutris_game.save()
        similar_name_count = Game.objects.filter(name=steam_game.name).count()
        if similar_name_count == 1:
            stats["same_name_exists"] += 1
        if similar_name_count > 1:
            stats["ambiguous_name"] += 1
    save_action_log("match_steam_games", stats)
    return stats
