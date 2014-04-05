import logging
import urllib2
import requests
from django.template.defaultfilters import slugify
from django.conf import settings
from games.models import Game

LOGGER = logging.getLogger(__name__)
STEAM_API_URL = "http://api.steampowered.com/"


def get_capsule(steamid):
    steam_cdn = "http://cdn2.steampowered.com"
    capsule_url = steam_cdn + "/v/gfx/apps/%d/capsule_184x69.jpg"
    return urllib2.urlopen(capsule_url % steamid).read()


def get_image(appid, img_logo_url):
    img_url = (
        "http://media.steampowered.com/"
        "steamcommunity/public/images/apps/{}/{}.jpg".format(
            appid, img_logo_url
        )
    )
    return urllib2.urlopen(img_url).read()


def steam_sync(steamid):
    get_owned_games = (
        "IPlayerService/GetOwnedGames/v0001/"
        "?key={}&steamid={}&format=json&include_appinfo=1"
        "&include_played_free_games=1".format(
            settings.STEAM_API_KEY, steamid
        )
    )
    steam_games_url = STEAM_API_URL + get_owned_games
    response = requests.get(steam_games_url)
    if response.status_code > 400:
        raise ValueError("Invalid response from steam: %s", response)
    json_data = response.json()
    response = json_data['response']
    if 'games' in response:
        return response['games']
    else:
        LOGGER.error("No games in response: %s", response)
        return []


def create_game(game):
    """ Create game object from Steam API call """
    slug = slugify(game['name'])[:50]
    LOGGER.info("Adding %s to library" % game['name'])
    steam_game = Game(
        name=game['name'],
        steamid=game['appid'],
        slug=slug,
    )
    if game['img_logo_url']:
        steam_game.get_steam_logo(game['img_logo_url'])
    steam_game.get_steam_icon(game['img_icon_url'])
    try:
        steam_game.save()
    except Exception as ex:
        LOGGER.error("Error while saving game %s: %s", game, ex)
        raise
    return steam_game
