"""GOG functions"""
import json
import logging
import os
import re
import time
from collections import defaultdict

import requests
from django.conf import settings
from django.utils import timezone

from common.util import get_auto_increment_slug, slugify
from games.models import Company, Game
from providers import models

LOGGER = logging.getLogger(__name__)


def get_or_create_company(game, field="publisher"):
    """Create a publisher from a GOGDB entry"""
    publisher_slug = slugify(game.metadata.get(field, ""))
    if not publisher_slug:
        return None
    publisher, created = Company.objects.get_or_create(slug=publisher_slug)
    if created:
        publisher.name = game.metadata[field]
        publisher.save()
    return publisher


def match_from_gog_api():
    """Match GOG API games with Lutris games"""
    stats = {
        "created": 0,
        "present": 0,
        "ambiguous": 0,
        "matched_exact": 0,
        "matched_case_insensitive": 0,
        "matched_alias": 0,
        "matched_tm": 0
    }
    for provider_game in models.ProviderGame.objects.filter(provider__name="gog"):
        if provider_game.games.count():
            if provider_game.games.count() > 1:
                stats["ambiguous"] += 1
            stats["present"] += 1
            continue
        # Check if a Lutris game exists

        queries = {
            "exact": Game.objects.filter(name=provider_game.name),
            "case_insensitive": Game.objects.filter(name__iexact=provider_game.name),
            "alias": Game.objects.filter(aliases__name__iexact=provider_game.name),
            "tm": Game.objects.filter(name__iexact=provider_game.name.replace("™", "")),
        }
        matched = False
        for strategy, query in queries.items():
            if matched:
                continue
            existing_games = query.exclude(change_for__isnull=False).order_by('id').distinct('id')
            if existing_games:
                stats["matched_%s" % strategy] += 1
                for lutris_game in existing_games:
                    lutris_game.provider_games.add(provider_game)
                matched = True
        if matched:
            continue

        release_date = provider_game.metadata["_embedded"]["product"].get("globalReleaseDate")
        if release_date:
            year = int(release_date[:4])
        else:
            year = None
        lutris_game = Game.objects.create(
            name=provider_game.name,
            slug=get_auto_increment_slug(Game, None, provider_game.name),
            year=year,
            is_public=True,
            gogid=provider_game.slug
        )
        stats["created"] += 1
        lutris_game.provider_games.add(provider_game)
    return stats


def fetch_gog_games_page(page):
    """Saves one page of GOG API results to disk"""
    LOGGER.info("Saving GOG API page %s", page)
    url = f"https://api.gog.com/v2/games?locale=en-US&page={page}&limit=50"
    response = requests.get(url)
    response_data = response.json()
    with open(
            os.path.join(settings.GOG_CACHE_PATH, f"{page}.json"), "w", encoding="utf-8"
    ) as json_file:
        json.dump(response_data, json_file, indent=2)
    return response_data


def cache_gog_games():
    """Cache the full GOG API to disk."""
    if not os.path.isdir(settings.GOG_CACHE_PATH):
        os.makedirs(settings.GOG_CACHE_PATH)
    response = fetch_gog_games_page(1)
    pages = response["pages"]
    for page in range(2, pages + 1):
        time.sleep(0.1)
        fetch_gog_games_page(page)


def iter_gog_items():
    """Iterate through GOG items, no matter the type"""
    num_pages = len(
        [f for f in os.listdir(settings.GOG_CACHE_PATH) if re.match(r"(\d+)\.json", f)]
    )
    for page in range(1, num_pages + 1):
        with open(
                os.path.join(settings.GOG_CACHE_PATH, f"{page}.json"), encoding="utf-8"
        ) as json_file:
            api_results = json.load(json_file)
            for item in api_results["_embedded"]["items"]:
                yield item


def iter_gog_games():
    """Iterate through all GOG games"""
    for item in iter_gog_items():
        is_installable = item["_embedded"]["product"]["isInstallable"]
        is_in_catalog = item["_embedded"]["product"]["isVisibleInAccount"]
        product_type = item["_embedded"]["productType"]
        if product_type == "GAME" and is_installable and is_in_catalog:
            yield item


def get_game_packages():
    """Return a list of game IDs and their corresponding package"""
    game_packages = defaultdict(list)
    for game in iter_gog_items():
        product_type = game["_embedded"]["productType"]
        if product_type == "PACK":
            for_sale = game["_embedded"]["product"]["isAvailableForSale"]
            if not for_sale:
                continue
            store_url = game["_links"]["store"]["href"]
            if not store_url:
                continue
            matches = re.search(r"game/([\w\d_]+)", store_url)
            store_id = matches.groups()[0]
            for game_url in game["_links"].get("includesGames", []):
                matches = re.search(r"games/(\d+)", game_url["href"])
                game_id = matches.groups()[0]
                game_packages[game_id].append(store_id)
    return game_packages



def verify_gogid_uniqueness():
    """Check that every GOG ID is unique"""
    duplicate_ids = set()
    for lutris_game in Game.objects.filter(gogid__isnull=False):
        try:
            Game.objects.get(gogid=lutris_game.gogid)
        except Game.MultipleObjectsReturned:
            duplicate_ids.add(lutris_game.gogid)
            LOGGER.warning(
                "Games shoudn't share a gogid %s (%s): %s",
                lutris_game.name,
                lutris_game.year,
                lutris_game.gogid
            )
    return duplicate_ids


def load_games_from_gog_api():
    """Load GOG games from the local cache to provider games
    Make sure the GOG cache is up to date!
    """
    stats = {
        "deleted": 0,
        "created": 0,
        "updated": 0,
    }
    provider = models.Provider.objects.get(name="gog")
    update_started_at = timezone.now()
    for game in iter_gog_games():
        gog_id = game["_embedded"]["product"]["id"]
        title = game["_embedded"]["product"]["title"]
        gog_game, created = models.ProviderGame.objects.get_or_create(
            provider=provider,
            slug=gog_id
        )
        gog_game.internal_id = gog_id
        gog_game.name = title
        gog_game.provider = provider
        gog_game.metadata = game
        gog_game.updated_at = update_started_at
        gog_game.save()
        if created:
            stats["created"] += 1
        else:
            stats["updated"] += 1
    delete_result = models.ProviderGame.objects.filter(
        provider=provider,
        updated_at__lt=update_started_at
    ).delete()
    stats["deleted"] = delete_result[0]
    delete_result = models.ProviderGame.objects.filter(
        provider=provider,
        updated_at__isnull=True
    ).delete()
    stats["deleted"] += delete_result[0]
    return stats


def populate_gogid_and_gogslug():
    """Fills the gogid and gogslug fields in games, respecting GOG packages"""
    packages = get_game_packages()
    stats = defaultdict(int)
    for gog_game in models.ProviderGame.objects.filter(provider__name="gog"):
        num_lutris_games = 0
        for lutris_game in gog_game.games.all():
            num_lutris_games += 1
            if not lutris_game.gogid:
                lutris_game.gogid = gog_game.slug
                stats["no_gog_id"] += 1
            if num_lutris_games > 1:
                stats["duplicates"] += 1
            if gog_game.slug in packages:
                lutris_game.gogslug = packages[gog_game.slug][0]
                stats["in_packages"] += 1
            else:
                store_url = gog_game.metadata["_links"]["store"]["href"]
                if store_url:
                    matches = re.search(r"game/([\w\d_]+)", store_url)
                    lutris_game.gogslug = matches.groups()[0]
                else:
                    LOGGER.warning("No store URL for %s", gog_game.name)
                    stats["no_store_url"] += 1
                    lutris_game.gogslug = ""
            lutris_game.save()
            stats["saved"] += 1
    return stats
