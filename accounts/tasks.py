import logging

from celery import task
from django.contrib.auth.models import User

import games.models

LOGGER = logging.getLogger()


@task
def sync_steam_library(user_id):
    user = User.objects.get(pk=user_id)
    steamid = user.get_profile().steamid
    steam_games = games.util.steam.steam_sync(steamid)
    for game in steam_games:
        try:
            steam_game = games.models.Game.objects.get(steamid=game['appid'])
        except games.models.Game.DoesNotExist:
            if not game['img_icon_url']:
                continue
            steam_game = games.models.Game(
                name=game['name'],
                steamid=game['appid'],
            )
            if game['img_logo_url']:
                steam_game.get_steam_logo(game['img_logo_url'])
            steam_game.get_steam_icon(game['img_icon_url'])
            steam_game.save()
        library = games.models.GameLibrary.objects.get(user=user)
        library.games.add(steam_game)
