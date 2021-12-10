"""GOG related utilities"""
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from common.util import crop_banner, slugify
from games.models import Game, Genre
from platforms.models import Platform

GOG_CACHE_PATH = "gog_cache"
LOGGER = logging.getLogger(__name__)


def download_logo(gog_game, dest_path, formatter="398_2x"):
    """Downloads all game logos from GOG

    Args:
        gog_game (dict): GOG game details from the API
        dest_path (str): where to save the logo
        formatter (str): Image size to download. Other used
                         values on the GOG website are 256 and 195
    """
    response = requests.get(f"https:{gog_game['image']}_product_tile_{formatter}.jpg")
    with open(dest_path, "wb") as logo_file:
        logo_file.write(response.content)
    LOGGER.info("Saved image for %s to %s", gog_game["slug"], dest_path)


def get_logo(gog_game, formatter="398_2x"):
    """Return the content of the GOG logo (cropped to Lutris ratio)"""
    logo_filename = f"{gog_game['id']}_{formatter}.jpg"

    # Get the logo from GOG
    gog_logo_path = os.path.join(settings.GOG_LOGO_PATH, logo_filename)
    if not os.path.exists(gog_logo_path):
        download_logo(gog_game, gog_logo_path)

    # Cropping the logo to lutris dimensions
    logo_path = os.path.join(settings.GOG_LUTRIS_LOGO_PATH, logo_filename)
    if not os.path.exists(logo_path):
        LOGGER.info("Cropping %s", logo_path)
        crop_banner(os.path.join(settings.GOG_LOGO_PATH, logo_filename), logo_path)
    with open(logo_path, "rb") as logo_file:
        content = logo_file.read()
    return content


def clean_name(name):
    """Remove some special characters from game titles to allow for easier comparison"""
    return name.replace("™", "").replace("®", "").strip()


def clean_gog_slug(gog_game):
    """Return a lutris like slug from a GOG game"""
    gog_slug = gog_game["slug"]
    gog_title = clean_name(gog_game["title"]).lower()
    cleaned_slug = gog_slug.replace("_", "-")
    if gog_slug.endswith("_a") and gog_title.startswith("a "):
        cleaned_slug = "a-" + cleaned_slug[:-2]
    if gog_slug.endswith("_the") and gog_title.startswith("the "):
        cleaned_slug = "the-" + cleaned_slug[:-4]
    return cleaned_slug


def fetch_gog_games_page(page):
    """Saves one page of GOG games to disk"""
    print(f"Saving page {page}")
    url = f"https://embed.gog.com/games/ajax/filtered?mediaType=game&page={page}"
    response = requests.get(url)
    response_data = response.json()
    with open(
        os.path.join(GOG_CACHE_PATH, f"{page}.json"), "w", encoding="utf-8"
    ) as json_file:
        json.dump(response_data, json_file, indent=2)
    return response_data


def cache_gog_games():
    """Cache all GOG games to disk"""
    response = fetch_gog_games_page(1)
    pages = response["totalPages"]
    for page in range(2, pages + 1):
        time.sleep(0.3)
        fetch_gog_games_page(page)


def iter_gog_games():
    """Iterate through all GOG games from a local cache"""
    excluded_suffixes = (
        "_soundtrack",
        "_soundtrack_remastered",
        "_ost",
        "_extras",
        "_demo",
        "_pack",
        "_dlc",
        "_season_pass",
    )
    num_pages = len(
        [f for f in os.listdir(GOG_CACHE_PATH) if re.match(r"(\d+)\.json", f)]
    )
    for page in range(1, num_pages + 1):
        with open(
            os.path.join(GOG_CACHE_PATH, f"{page}.json"), encoding="utf-8"
        ) as json_file:
            api_results = json.load(json_file)
            for product in api_results["products"]:
                if not product["slug"].endswith(excluded_suffixes):
                    yield product


def iter_lutris_games_by_gog_slug():
    """Iterate through Lutris games that have a valid GOG slug"""
    for gog_game in iter_gog_games():
        for game in Game.objects.filter(gogslug=gog_game["slug"]):
            yield (game, gog_game)


def iter_games_by_lutris_slug():
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


def inspect_gog_game(gog_game):
    """Fix problems with gog games"""

    gogid = gog_game["id"]

    # Fix duplicates GOG IDs
    lutris_games = Game.objects.filter(gogid=gogid)
    for game in lutris_games:
        LOGGER.info("%s (%s) created: %s", game, game.year, game.created)
        LOGGER.info("https://lutris.net%s", game.get_absolute_url())
        if timezone.now() - game.created < timedelta(days=1):
            LOGGER.warning("Deleting %s as it was just created", game)
            game.delete()


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
            LOGGER.warning("Games shoudn't share a gogid (id: %s)", gog_game["id"])
            inspect_gog_game(gog_game)
        slug_counter += 1
    LOGGER.error(
        "Found %s games by ID and saved %s ID to games", slug_counter, id_counter
    )


def sync_ids_by_slug():
    game_counter = 0
    for game, gog_game in iter_games_by_lutris_slug():
        LOGGER.info("Syncing GOG ID for %s", game)
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
            is_public=True,
        )
    except IntegrityError:
        LOGGER.warning("Game %s is already in Lutris!", slugify(name))
        game = Game.objects.get(slug=slugify(name))
        game.gogid = gog_game["id"]
        game.gogslug = gog_game["slug"]
    game.set_logo_from_gog(gog_game)
    if gog_game["worksOn"]["Linux"]:
        platform = Platform.objects.get(slug="linux")
    else:
        platform = Platform.objects.get(slug="windows")
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
