"""Sync Steam games"""

import time
from simplejson import JSONDecodeError
import requests
from celery.utils.log import get_task_logger
from django.utils import timezone

from common.models import save_action_log
from games.models import Game
from games.webhooks import send_simple_message
from lutrisweb.celery import app
from providers import models

LOGGER = get_task_logger(__name__)


ALL_APPS_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/?"
APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails?appids="


class RateLimitExceeded(Exception):
    """Raised when the Steam API rate limit is exceeded"""


@app.task
def load_steam_games():
    """Query the Steam API and load every game as a ProviderGame"""
    provider = models.Provider.objects.get(name="steam")
    response = requests.get(ALL_APPS_URL)
    if response.status_code != 200 or not response.text:
        LOGGER.warning("Steam API returned empty or bad response: %s", response.status_code)
        return {"error": "Steam API unavailable"}
    try:
        game_list = response.json()["applist"]["apps"]
    except (JSONDecodeError, KeyError) as ex:
        LOGGER.warning("Failed to parse Steam API response: %s", ex)
        return {"error": str(ex)}
    stats = {"created": 0, "updated": 0}
    for game in game_list:
        provider_game, created = models.ProviderGame.objects.get_or_create(
            slug=game["appid"], provider=provider
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
    send_simple_message("Steam games loaded: %s" % stats)
    return stats


@app.task
def match_steam_games():
    """Match Steam provider games with those imported from user libraries"""
    stats = {
        "matched": 0,
        "same_name_exists": 0,
        "ambiguous_name": 0,
    }
    for steam_game in models.ProviderGame.objects.filter(
        provider__name="steam", games__isnull=True
    ):
        existing_games = Game.objects.filter(steamid=steam_game.internal_id)
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
    send_simple_message("Steam games matched: %s" % stats)
    return stats


@app.task
def fetch_app_details(appid):
    details_response = requests.get(APP_DETAILS_URL + appid)
    if details_response.status_code == 429:
        raise RateLimitExceeded
    if details_response.status_code != 200:
        LOGGER.warning(
            "Invalid response for appid %s: %s", appid, details_response.status_code
        )
        return False
    try:
        details = details_response.json()
    except JSONDecodeError:
        LOGGER.warning("Invalid JSON for appid %s: %s", appid, details_response.text)
        return False
    game = models.ProviderGame.objects.get(provider__name="steam", internal_id=appid)
    success = details[appid]["success"]
    if not success:
        game.metadata = details
    else:
        game.metadata = details[appid]["data"]
        LOGGER.info("App details for Steam game %s (%s)", game.name, game.internal_id)
    game.updated_at = timezone.now()
    game.save()
    return success


@app.task
def fetch_app_details_all(max_games=200):
    stats = {"fetched": 0, "failed": 0}
    for index, game in enumerate(
        models.ProviderGame.objects.filter(
            provider__name="steam", metadata__isnull=True
        )
    ):
        try:
            success = fetch_app_details(game.slug)
        except RateLimitExceeded:
            time.sleep(60)
            success = fetch_app_details(game.slug)
        time.sleep(1)
        if success:
            stats["fetched"] += 1
        else:
            stats["failed"] += 1
        if index > max_games:
            break
    send_simple_message("Steam details fetched: %s" % stats)
