import urllib2
import requests
#from django.conf import settings


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
    STEAM_API_KEY = "FEC1EEECA360B64106F36656332A9B73"
    steamid = "76561197970308221"
    get_owned_games = (
        "IPlayerService/GetOwnedGames/v0001/"
        "?key={}&steamid={}&format=json&include_appinfo=1"
        "&include_played_free_games=1".format(
            STEAM_API_KEY, steamid
        )
    )
    response = requests.get(STEAM_API_URL + get_owned_games)
    return response.json()['response']['games']
