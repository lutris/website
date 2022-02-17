"""GOG functions"""
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.db import IntegrityError

from common.util import get_auto_increment_slug, slugify
from games.models import Company, Game, Genre
from platforms.models import Platform
from providers import models

LOGGER = logging.getLogger(__name__)


def clean_name(name):
    """Removed unwanted info from GOG game names"""
    extras = (
        "demo",
        "gold pack",
        "complete pack",
        "the final cut",
        "enhanced edition",
        "free preview",
        "complete edition",
        "alpha version",
        "pc edition",
        "ultimate edition",
        "commander pack",
        "gold edition",
        "drm free edition",
        "directx 11 version",
        "remake",
        "original game soundtrack",
        "soundtrack",
        "cd version",
        "deluxe edition",
        "galaxy edition",
        "complete",
    )
    for extra in extras:
        if name.strip(")").lower().endswith(extra):
            name = name[:-len(extra)].strip(" -:®™(").replace("™", "")
    return name


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


def iter_lutris_games_by_gog_slug():
    """Iterate through Lutris games that have a valid GOG slug"""
    for gog_game in iter_gog_games():
        for game in Game.objects.filter(gogslug=gog_game["slug"]):
            yield (game, gog_game)


def fetch_gog_games_page(page):
    """Saves one page of GOG API results to disk"""
    LOGGER.info("Saving page %s", page)
    url = f"https://embed.gog.com/games/ajax/filtered?mediaType=game&page={page}"
    response = requests.get(url)
    response_data = response.json()
    with open(
        os.path.join(settings.GOG_CACHE_PATH, f"{page}.json"), "w", encoding="utf-8"
    ) as json_file:
        json.dump(response_data, json_file, indent=2)
    return response_data


def cache_gog_games():
    """Cache the full GOG API to disk.
    Note that this API doesn't expose games present in a package so it is not recommended
    to use it. Instead, get the GOG library from GOGDB, which has IDs for all games and
    not only packages."""
    LOGGER.warning("Querying games from the game store API (This is not recommended)")
    if not os.path.isdir(settings.GOG_CACHE_PATH):
        os.makedirs(settings.GOG_CACHE_PATH)
    response = fetch_gog_games_page(1)
    pages = response["totalPages"]
    for page in range(2, pages + 1):
        time.sleep(0.3)
        fetch_gog_games_page(page)


def iter_gog_games():
    """Iterate through all GOG products stored locally."""
    LOGGER.warning("Iterating GOG products from the GOG store API, this may not yield all games")
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
        [f for f in os.listdir(settings.GOG_CACHE_PATH) if re.match(r"(\d+)\.json", f)]
    )
    for page in range(1, num_pages + 1):
        with open(
            os.path.join(settings.GOG_CACHE_PATH, f"{page}.json"), encoding="utf-8"
        ) as json_file:
            api_results = json.load(json_file)
            for product in api_results["products"]:
                if not product["slug"].endswith(excluded_suffixes):
                    yield product

def load_games_from_gog_api():
    """Load GOG games from the local cache to provider games"""
    cache_gog_games()
    provider = models.Provider.objects.get(name="gog")
    update_started_at = timezone.now()
    for game in iter_gog_games():
        gog_game, created = models.ProviderGame.objects.get_or_create(
            provider=provider,
            slug=game["id"]
        )
        gog_game.name = game["title"]
        gog_game.provider = provider
        gog_game.metadata = game
        gog_game.save()
        if created:
            LOGGER.info("Created new provider game %s", game["title"])
    old_provider_games = models.ProviderGame.objects.filter(
        provider=provider,
        updated_at__lt=update_started_at
    )
    LOGGER.info("Deleting %d old games", old_provider_games.count())
    for game in old_provider_games:
        game.delete()


def load_games_from_gogdb(file_path):
    """Generate ProviderGames for GOG from a GOGDB dump"""
    LOGGER.info("Loading GOG games from %s", file_path)
    provider = models.Provider.objects.get(name="gog")
    update_started_at = timezone.now()
    with open(file_path, encoding="utf-8") as list_file:
        game_list = json.load(list_file)
    stats = {
        "skipped": 0,
        "created": 0,
        "updated": 0,
        "deleted": 0,
    }
    for game in game_list:
        if "product_id" not in game:
            stats["skipped"] += 1
            continue
        provider_game, created = models.ProviderGame.objects.get_or_create(
            slug=game["product_id"],
            provider=provider
        )
        provider_game.name = game["name"]
        provider_game.metadata = game
        provider_game.save()
        if created:
            stats["created"] += 1
        else:
            stats["updated"] += 1
    old_provider_games = models.ProviderGame.objects.filter(
        provider=provider,
        updated_at__lt=update_started_at
    )
    stats["deleted"] = old_provider_games.count()
    LOGGER.info("Deleting %d old games", old_provider_games.count())
    for game in old_provider_games:
        game.delete()
    return stats

def match_with_lutris(game):
    """Matching Lutris games with a GOG game"""
    game_name = clean_name(game.name)
    existing_games = Game.objects.filter(
        Q(name=game_name)
        | Q(gogid=game.slug)
        | Q(slug=slugify(game_name))
        | Q(aliases__name=game_name)
    ).exclude(change_for__isnull=False).order_by('id').distinct('id')
    if len(existing_games) > 1:
        LOGGER.warning("Duplicates found for %s: %s", game, existing_games)
    matches = []
    for existing_game in existing_games:
        existing_game.provider_games.add(game)
        matches.append(existing_game)
    return matches


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


def create_game_from_gog_api(gog_game):
    """Creates a Lutris game from a GOG API game"""
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


def inspect_gog_game(gog_game):
    """Delete most recent copies of a game with a duplicated GOG ID"""
    # Fix duplicates GOG IDs
    for game in Game.objects.filter(gogid=gog_game["id"]):
        LOGGER.info("%s (%s) created: %s", game, game.year, game.created)
        LOGGER.info("https://lutris.net%s", game.get_absolute_url())
        if timezone.now() - game.created < timedelta(days=1):
            LOGGER.warning("Deleting %s as it was just created", game)
            game.delete()


def sync_slugs_with_ids():
    """Set GOG IDs to games by matching them by slug"""
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
    LOGGER.error("Found %s games by ID and saved %s ID to games", slug_counter, id_counter)


def iter_orphan_gog_games():
    """Iterate over GOG games that have no associated Lutris game"""
    for gog_game in iter_gog_games():
        if gog_game["type"] != 1:
            # Exclude special editions and DLCs
            continue
        if not Game.objects.filter(gogid=gog_game["id"]).count():
            yield gog_game

def iter_games_by_lutris_slug():
    """Iterate over Lutris games that match a cleaned versio of the GOG slug"""
    for gog_game in iter_gog_games():
        for game in Game.objects.filter(slug=clean_gog_slug(gog_game)):
            if not game.gogid:
                yield (game, gog_game)


def sync_ids_by_slug():
    """Give GOG ID and slug to games with a match"""
    game_counter = 0
    for game, gog_game in iter_games_by_lutris_slug():
        LOGGER.info("Syncing GOG ID for %s", game)
        game.gogslug = gog_game["slug"]
        game.gogid = gog_game["id"]
        game.save()
        game_counter += 1
    LOGGER.info("Synced %s games", game_counter)




def sync_all_gog_games():
    """Read cached GOG files and matches the games against Lutris games"""

    sync_slugs_with_ids()

    # CAUTION! This can cause some mismatchs
    # sync_ids_by_slug()

    i = 0
    for gog_game in iter_orphan_gog_games():
        game = create_game_from_gog_api(gog_game)
        if not game:
            continue
        if not game.title_logo:
            raise RuntimeError("No")
        LOGGER.info("Created game %s", game)
        i += 1
    LOGGER.info("%d games created", i)



def match_from_gog_api():
    """Match GOG API games with Lutris games"""
    stats = {
        "created": 0,
        "present": 0,
        "not_game": 0,
        "matched": 0,
    }
    for provider_game in models.ProviderGame.objects.filter(provider__name="gog"):
        if provider_game.games.count():
            stats["present"] += 1
            continue
        if provider_game.metadata["type"] != 1:
            # Game has been matched already or is not a game
            stats["not_game"] += 1
            continue
        # Check if a Lutris game exists
        game_name = clean_name(provider_game.name)
        existing_games = Game.objects.filter(
            Q(name=game_name)
            | Q(slug=slugify(game_name))
            | Q(aliases__name=game_name)
        ).exclude(change_for__isnull=False).order_by('id').distinct('id')
        for lutris_game in existing_games:
            LOGGER.info("GOG game %s matched with %s", provider_game, lutris_game)
            lutris_game.provider_games.add(provider_game)
        if existing_games.count():
            stats["matched"] += 1
            continue
        LOGGER.info("Creating %s", game_name)
        if provider_game.metadata.get("releaseDate"):
            year = datetime.fromtimestamp(provider_game.metadata["releaseDate"]).year
        else:
            year = None
        lutris_game = Game.objects.create(
            name=game_name,
            slug=get_auto_increment_slug(Game, None, game_name),
            year=year,
            is_public=True,
            gogid=provider_game.slug
        )
        stats["created"] += 1
        lutris_game.provider_games.add(provider_game)
    LOGGER.info(stats)
    return stats



def match_from_gogdb(create_missing=False):
    """Match GOG games from GOGDB to Lutris games"""
    stats = {
        "present": 0,
        "created": 0,
        "matched": 0,
        "total": 0,
        "unmatched": 0,
    }
    for game in models.ProviderGame.objects.filter(provider__name="gog"):
        stats["total"] += 1
        product_type = game.metadata.get("product_type")
        if product_type != "Game":
            LOGGER.debug("Skipping content type %s for %s", product_type, game)
            continue
        if game.games.count():
            stats["present"] += 1
            continue
        matches = match_with_lutris(game)
        if matches:
            stats["matched"] += 1
        elif create_missing:
            lutris_game = Game.objects.create(
                name=game.name,
                slug=get_auto_increment_slug(Game, None, game.name),
                publisher=get_or_create_company(game, "publisher"),
                developer=get_or_create_company(game, "developers"),
                is_public=True,
                gogid=game.slug
            )
            lutris_game.provider_games.add(game)
            stats["created"] += 1
            LOGGER.info("Created %s from %s", lutris_game, game)
        else:
            stats["unmatched"] += 1
            LOGGER.warning("No match found for %s", game.metadata)
    return stats
