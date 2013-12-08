import logging

from celery import task
from django.template.defaultfilters import slugify

import games.models
from accounts.models import User

LOGGER = logging.getLogger()


def create_game(game):
    LOGGER.info("Adding %s to library" % game['name'])
    steam_game = games.models.Game(
        name=game['name'],
        steamid=game['appid'],
        slug=slugify(game['name'])[50:],
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


@task
def sync_steam_library(user_id):
    user = User.objects.get(pk=user_id)
    steamid = user.steamid
    steam_games = games.util.steam.steam_sync(steamid)
    library = games.models.GameLibrary.objects.get(user=user)
    for game in steam_games:
        LOGGER.info("Adding %s to %s's library", game['name'], user.username)
        if not game['img_icon_url']:
            LOGGER.info("Game %s has no icon" % game['name'])
            continue
        try:
            steam_game = games.models.Game.objects.get(steamid=game['appid'])
        except games.models.Game.DoesNotExist:
            pass
        else:
            try:
                steam_game = games.models.Game.objects.get(
                    slug=slugify(game['name'])[50:]
                )
                steam_game.appid = game['appid']
                steam_game.save()
            except games.models.Game.DoesNotExist:
                steam_game = create_game(game)
        library.games.add(steam_game)
