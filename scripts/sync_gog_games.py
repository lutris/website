""" Compare GOG games to the Lutris library """
import os
import re
import json
import time
import logging
from datetime import datetime

import requests
from django.db.utils import IntegrityError

from games.models import Game, Genre
from platforms.models import Platform
from common.util import slugify


GOG_CACHE_PATH = 'gog-cache'

LOGGER = logging.getLogger(__name__)


def clean_name(name):
    """Remove some special characters from game titles to allow for easier comparison"""
    return name.replace('™', '').replace('®', '').strip()


def clean_gog_slug(gog_game):
    """Return a lutris like slug from a GOG game"""
    gog_slug = gog_game['slug']
    gog_title = clean_name(gog_game['title']).lower()
    cleaned_slug = gog_slug.replace('_', '-')
    if gog_slug.endswith('_a') and gog_title.startswith('a '):
        cleaned_slug = 'a-' + cleaned_slug[:-2]
    if gog_slug.endswith('_the') and gog_title.startswith('the '):
        cleaned_slug = 'the-' + cleaned_slug[:-4]
    LOGGER.info(cleaned_slug)
    return cleaned_slug


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
    """Iterate through all GOG games from their API"""
    excluded_suffixes = (
        "_soundtrack",
        "_soundtrack_remastered",
        "_ost",
        "_extras",
        "_demo",
        "_pack",
        "_dlc",
        "_season_pass"
    )
    num_pages = len([f for f in os.listdir(GOG_CACHE_PATH) if re.match(r'(\d+)\.json', f)])
    for page in range(1, num_pages + 1):
        with open(os.path.join(GOG_CACHE_PATH, "{}.json".format(page))) as json_file:
            api_results = json.load(json_file)
            for product in api_results['products']:
                if not product["slug"].endswith(excluded_suffixes):
                    yield product


def iter_lutris_games_by_gog_slug():
    """Iterate through Lutris games that have a valid GOG slug"""
    for gog_game in iter_gog_games():
        for game in Game.objects.filter(gogslug=gog_game["slug"]):
            yield (game, gog_game)


def iter_lutris_games_by_lutris_slug():
    for gog_game in iter_gog_games():
        for game in Game.objects.filter(slug=clean_gog_slug(gog_game)):
            if not game.gogid:
                yield (game, gog_game)


def iter_orphan_gog_games():
    for gog_game in iter_gog_games():
        if gog_game["type"] != 1:
            # Exclude special editions and DLCs
            continue
        if not Game.objects.filter(gogid=gog_game["id"]).count():
            yield gog_game



def sync_slugs_with_ids():
    slug_counter = 0
    id_counter = 0
    for game, gog_game in iter_lutris_games_by_gog_slug():
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


def create_game(gog_game):
    """Creates a Lutris game from a GOG game"""
    name = clean_name(gog_game["title"])
    try:
        game = Game.objects.create(
            name=name,
            slug=slugify(name),
            gogid=gog_game["id"],
            gogslug=gog_game["slug"],
            is_public=True
        )
    except IntegrityError:
        LOGGER.warning("Game %s is already in Lutris!", slugify(name))
        game = Game.objects.get(slug=slugify(name))
        game.gogid = gog_game["id"]
        game.gogslug = gog_game["slug"]
    game.set_logo_from_gog(gog_game)
    if gog_game["worksOn"]["Linux"]:
        platform = Platform.objects.get(slug='linux')
    else:
        platform = Platform.objects.get(slug='windows')
    game.platforms.add(platform)
    for gog_genre in gog_game["genres"]:
        genre, created = Genre.objects.get_or_create(slug=slugify(gog_genre))
        if created:
            genre.name = gog_genre
            LOGGER.info("Created genre %s", genre.name)
            genre.save()
        game.genres.add(genre)

    if gog_game["releaseDate"]:
        release_date = datetime.fromtimestamp(gog_game["releaseDate"])
        game.year = release_date.year

    game.save()
    return game


def run():
    """Read cached GOG files and matches the games against Lutris games"""

    if not os.path.isdir('gog_cache'):
        os.makedirs('gog_cache')
        cache_gog_games()

    sync_slugs_with_ids()
    sync_ids_by_slug()

    i = 0
    for gog_game in iter_orphan_gog_games():
        game = create_game(gog_game)
        if not game:
            continue
        if not game.title_logo:
            raise RuntimeError("No")
        LOGGER.info("Created game %s", game)
        i += 1
    LOGGER.info("%d games created", i)
