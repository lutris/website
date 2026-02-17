"""Steam related utilities"""

import logging
from json import JSONDecodeError
import requests
from django.conf import settings

from games import models
from accounts.models import User
from common.util import slugify

LOGGER = logging.getLogger(__name__)
STEAM_API_URL = "https://api.steampowered.com/"
STEAM_CDN = "http://cdn.akamai.steamstatic.com"


def get_capsule(steamid):
    """Download Steam 'capsule' for a given appid"""
    capsule_url = STEAM_CDN + "/steam/apps/%s/capsule_184x69.jpg"
    response = requests.get(capsule_url % steamid)
    return response.content


def get_image(appid, img_logo_url):
    img_url = (
        "http://media.steampowered.com/"
        "steamcommunity/public/images/apps/{}/{}.jpg".format(appid, img_logo_url)
    )
    response = requests.get(img_url)
    return response.content


def steam_sync(steamid):
    """Get a user's (referenced by their SteamID) Steam library"""
    get_owned_games = (
        "IPlayerService/GetOwnedGames/v0001/"
        "?key={}&steamid={}&format=json&include_appinfo=1"
        "&include_played_free_games=1".format(settings.STEAM_API_KEY, steamid)
    )
    steam_games_url = STEAM_API_URL + get_owned_games
    response = requests.get(steam_games_url)
    if response.status_code > 400:
        raise ValueError("Invalid response from steam: %s" % response)
    try:
        json_data = response.json()
    except JSONDecodeError:
        LOGGER.error("Invalid JSON response from Steam API: %s", response.content)
        return []
    response = json_data["response"]
    if not response:
        LOGGER.info("No games in response of %s", steam_games_url)
        return []
    if "games" in response:
        return response["games"]
    if "game_count" in response and response["game_count"] == 0:
        return []
    LOGGER.error("Unexpected response %s", json_data)
    return []


def create_game(game):
    """Create game object from Steam API call"""
    steam_game = models.Game(
        name=game["name"],
        steamid=game["appid"],
        slug=slugify(game["name"])[:50],
        is_public=True,
    )
    if game.get("img_logo_url"):
        steam_game.set_logo_from_steam_api(game["img_logo_url"])

    if game.get("img_icon_url"):
        steam_game.set_icon_from_steam_api(game["img_icon_url"])
    steam_game.save()
    return steam_game


def create_steam_installer(game):
    """Create a Lutris installer for a given game instance"""
    installer = models.Installer()
    installer.runner = models.Runner.objects.get(slug="steam")
    installer.user = User.objects.get(username="strider")
    installer.game = game
    installer.set_default_installer()
    installer.published = True
    installer.save()


def get_store_info(appid):
    """Return the Steam store information for a game by it's Steam ID"""
    response = requests.get(
        "https://store.steampowered.com/api/appdetails?appids=%s" % appid
    )
    if response.status_code != 200:
        LOGGER.warning(
            "Invalid response from the Steam store: %s", response.status_code
        )
        LOGGER.warning(response.content)
        return
    store_info = response.json()
    if not store_info.get(appid, {}).get("success"):
        LOGGER.warning("Unsuccessful response from Steam store for app %s", appid)
        LOGGER.warning(store_info)
        return
    return store_info[appid]["data"]
