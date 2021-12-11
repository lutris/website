"""GOG functions"""
import json
import logging
import os
import re
import time
import requests

GOG_CACHE_PATH = "gog_cache"
LOGGER = logging.getLogger(__name__)


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
    LOGGER.info("Saving page %s", page)
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
