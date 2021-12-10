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