import logging

from celery import task
from django.db import IntegrityError

import games.models
from games.notifier import send_daily_mod_mail
from games.util.steam import create_game
from accounts.models import User
from common.util import slugify

LOGGER = logging.getLogger()


@task
def sync_steam_library(user_id):
    user = User.objects.get(pk=user_id)
    steamid = user.steamid
    library = games.models.GameLibrary.objects.get(user=user)
    steam_games = games.util.steam.steam_sync(steamid)
    if not steam_games:
        LOGGER.info("Steam user %s has no steam games", user.username)
        return
    for game in steam_games:
        LOGGER.info("Adding %s to %s's library", game['name'], user.username)
        if not game['img_icon_url']:
            LOGGER.info("Game %s has no icon", game['name'])
            continue
        try:
            steam_game = games.models.Game.objects.get(steamid=game['appid'])
        except games.models.Game.MultipleObjectsReturned:
            LOGGER.error("Multiple games with appid '%s'", game['appid'])
            continue
        except games.models.Game.DoesNotExist:
            LOGGER.info("No game with steam id %s", game['appid'])
            try:
                steam_game = games.models.Game.objects.get(
                    slug=slugify(game['name'])[:50]
                )
                if not steam_game.steamid:
                    steam_game.steamid = game['appid']
                    steam_game.save()
            except games.models.Game.DoesNotExist:
                steam_game = create_game(game)
                LOGGER.info("Creating game %s", steam_game.slug)
        try:
            library.games.add(steam_game)
        except IntegrityError:
            # Game somehow already added.
            pass


@task
def daily_mod_mail():
    send_daily_mod_mail()
