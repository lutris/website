"""Celery tasks for user management"""
import logging

from django.db import IntegrityError

import games.models
from games.notifier import send_daily_mod_mail
from games.util.steam import create_game
from accounts.models import User
from accounts import spam_control
from common.util import slugify
from common.models import save_action_log
from lutrisweb.celery import app

LOGGER = logging.getLogger()


@app.task
def sync_steam_library(user_id):
    """Launch a Steam to Lutris library sync"""
    user = User.objects.get(pk=user_id)
    steamid = user.steamid
    library = games.models.GameLibrary.objects.get(user=user)
    steam_games = games.util.steam.steam_sync(steamid)
    game_count = 0
    if not steam_games:
        LOGGER.info("Steam user %s has no steam games", user.username)
        return
    for game in steam_games:
        if not game['img_icon_url']:
            LOGGER.info("Game %s has no icon", game['name'])
            continue
        game_count += 1
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
    LOGGER.info("Added %s Steam games to %s's library", game_count, user.username)


@app.task
def daily_mod_mail():
    """Send a daily moderation mail to moderators"""
    send_daily_mod_mail()


@app.task
def clear_spammers():
    """Delete spam accounts"""
    spam_website_deleted = spam_control.clear_users(spam_control.get_no_games_with_website())
    if spam_website_deleted:
        save_action_log("spam_website_deleted", spam_website_deleted)
    spam_avatar_deleted = spam_control.clear_users(spam_control.get_spam_avatar_users())
    if spam_avatar_deleted:
        save_action_log("spam_avatar_deleted", spam_avatar_deleted)


def deduplicate_library(self, username):
    buckets = {}
    for lg in games.models.LibraryGame.objects.filter(gamelibrary__user=username):
        if lg.slug in buckets:
            buckets[lg.slug].append(lg)
        else:
            buckets[lg.slug] = [lg]
    for slug, _games in buckets.items():
        game_info = {}
        other_game = {}
        if len(_games) == 1:
            continue
        for game in _games:
            if not game_info:
                game_info = {"slug": game.slug, "runner": game.runner, "lastplayed": game.lastplayed}
            else:
                other_game = {"slug": game.slug, "runner": game.runner, "lastplayed": game.lastplayed}
            if game_info == other_game:
                print("delete", game)
                game.delete()
