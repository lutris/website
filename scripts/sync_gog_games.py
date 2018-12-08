""" Compare GOG games to the Lutris library """
import os
import re
import json
import time
import logging
import requests

from games.models import Game

GOG_CACHE_PATH = 'gog_cache'
LOGGER = logging.getLogger(__name__)


def fetch_gog_games_page(page):
    """Saves one page of GOG games to disk"""
    print("Saving page %s" % page)
    url = "https://embed.gog.com/games/ajax/filtered?mediaType=game&page={}".format(page)
    response = requests.get(url)
    response_data = response.json()
    with open(os.path.join(GOG_CACHE_PATH, '{}.json'.format(page)), 'w') as json_file:
        json.dump(response_data, json_file, indent=2)
    return response_data


def cache_gog_games():
    """Cache all GOG games to disk"""
    response = fetch_gog_games_page(1)
    pages = response['totalPages']
    for page in range(2, pages + 1):
        time.sleep(0.3)
        fetch_gog_games_page(page)


def iter_gog_games():
    nopes = ("_soundtrack", "_ost", "_extras", "_pack", "_dlc")
    num_pages = len([f for f in os.listdir(GOG_CACHE_PATH) if re.match(r'(\d+)\.json', f)])
    for page in range(1, num_pages + 1):
        with open(os.path.join(GOG_CACHE_PATH, "{}.json".format(page))) as json_file:
            api_results = json.load(json_file)
            for product in api_results['products']:
                if not product["slug"].endswith(nopes):
                    yield product


def clean_name(name):
    return name.lower().replace('™', '').replace('®', '').replace(':', '').strip()


def compare_names(name_1, name_2):
    return clean_name(name_1) == clean_name(name_2)


def iter_lutris_games_by_gog_slug():
    for gog_game in iter_gog_games():
        for game in Game.objects.filter(gogslug=gog_game["slug"]):
            yield (game, gog_game)


def iter_lutris_games_by_lutris_slug():
    for gog_game in iter_gog_games():
        for game in Game.objects.filter(slug=gog_game["slug"].replace("_", "-")):
            if not game.gogid:
                yield (game, gog_game)


def iter_orphan_gog_games():
    for gog_game in iter_gog_games():
        games = Game.objects.filter(gogid=gog_game["id"])
        if not games:
            yield gog_game



def sync_slugs_with_ids():
    slug_counter = 0
    id_counter = 0
    for game, gog_game in iter_lutris_games_by_gog_slug():
        if not compare_names(game.name, gog_game["title"]):
            LOGGER.info("Title is different: '%s' and '%s'", game.name, gog_game["title"])
        try:
            game = Game.objects.get(gogid=gog_game["id"])
        except Game.DoesNotExist:
            game.gogid = gog_game["id"]
            game.save()
            id_counter += 1
            continue
        except Game.MultipleObjectsReturned:
            pass
        slug_counter += 1
    LOGGER.error("Found %s games by ID and saved %s ID to games", slug_counter, id_counter)


def sync_ids_by_slug():
    game_counter = 0
    for game, gog_game in iter_lutris_games_by_lutris_slug():
        LOGGER.info("Syncing GOG ID for %s", Game)
        game.gogslug = gog_game["slug"]
        game.gogid = gog_game["id"]
        game.save()
        game_counter += 1
    LOGGER.info("Synced %s games", game_counter)


def run():
    """Read cached GOG files and matches the games against Lutris games"""

    if not os.path.isdir('gog_cache'):
        os.makedirs('gog_cache')
        cache_gog_games()

    sync_slugs_with_ids()
    sync_ids_by_slug()

    # i = 0
    # for gog_game in iter_orphan_gog_games():
    #     print("https://gog.com" + gog_game["url"])
    #     i += 1
    # print(i)
