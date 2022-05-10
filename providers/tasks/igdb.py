"""Provider tasks"""
import os
import json
from datetime import datetime

import requests
from django.conf import settings
from django.core.files.base import ContentFile

from celery import task
from celery.utils.log import get_task_logger
from common.util import slugify
from games.models import Game
from platforms.models import Platform
from providers.igdb import IGDBClient, GAME_CATEGORIES
from providers.models import Provider, ProviderGame, ProviderGenre, ProviderPlatform, ProviderCover

LOGGER = get_task_logger(__name__)


def _igdb_loader(resource_name, model):
    """Generic function to load a collection from IGDB to database"""
    client = IGDBClient(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    client.get_authentication_token()
    if resource_name not in ("games", "covers"):
        client.page_size = 10  # Most endpoints don't seem to support large page sizes
    resources = True
    page = 1
    provider, _created = Provider.objects.get_or_create(name="igdb")
    while resources:
        LOGGER.info("Getting page %s of IGDB API", page)
        response = client.get_resources(f"{resource_name}/", page=page)
        try:
            resources = response.json()
        except json.JSONDecodeError:
            LOGGER.error("Failed to read JSON response: %s", response.text)
            continue
        for api_payload in resources:
            model.create_from_igdb_api(provider, api_payload)
        page += 1


@task
def load_igdb_games():
    """Load all games from IGDB"""
    _igdb_loader("games", ProviderGame)


@task
def load_igdb_genres():
    """Load all genres from IGDB"""
    _igdb_loader("genres", ProviderGenre)


@task
def load_igdb_platforms():
    """Load all platforms from IGDB"""
    _igdb_loader("platforms", ProviderPlatform)


@task
def load_igdb_covers():
    """Load all covers from IGDB"""
    _igdb_loader("covers", ProviderCover)


@task
def match_igdb_games():
    """Create or update Lutris games from IGDB games"""
    platforms = {
        p.igdb_id: p for p in Platform.objects.filter(igdb_id__isnull=False)
    }
    for igdb_game in ProviderGame.objects.filter(provider__name="igdb"):
        igdb_slug = igdb_game.metadata["slug"]
        # Only match main games
        if igdb_game.metadata["category"] != 0:
            LOGGER.info(
                "Skipping %s, category: %s",
                igdb_slug,
                GAME_CATEGORIES[igdb_game.metadata["category"]]
            )
            continue
        if not igdb_slug:
            LOGGER.error("Missing slug for %s", igdb_game.metadata)
            continue
        try:
            lutris_game = Game.objects.get(slug=igdb_slug)
            LOGGER.info("Updating Lutris game %s", igdb_game.name)
        except Game.DoesNotExist:
            LOGGER.info("Creating Lutris game %s", igdb_game.name)
            lutris_game = Game.objects.create(
                name=igdb_game.name,
                slug=igdb_slug,
            )
        if not lutris_game.year and igdb_game.metadata.get("first_release_date"):
            lutris_game.year = datetime.fromtimestamp(igdb_game.metadata["first_release_date"]).year

        if not lutris_game.description and igdb_game.metadata.get("summary"):
            lutris_game.description = igdb_game.metadata.get("summary")
        for platform_id in igdb_game.metadata.get("platforms", []):
            try:
                lutris_game.platforms.add(platforms[platform_id])
            except KeyError:
                LOGGER.warning("No platform with ID %s", platform_id)
                continue
        lutris_game.provider_games.add(igdb_game)
        lutris_game.is_public = True
        lutris_game.save()


@task
def sync_igdb_platforms():
    """Syncs IGDB platforms to Lutris"""
    for igdb_platform in ProviderPlatform.objects.filter(provider__name="igdb"):
        igdb_slug = igdb_platform.metadata["slug"]
        try:
            lutris_platform = Platform.objects.get(slug=igdb_slug)
        except Platform.DoesNotExist:
            lutris_platform = Platform.objects.create(
                name=igdb_platform.name,
                slug=igdb_slug
            )
        lutris_platform.igdb_id = igdb_platform.metadata["id"]
        lutris_platform.save()


def get_igdb_cover(image_id, size="cover_big"):
    """Download a cover from IGDB and return its contents"""
    url = f"https://images.igdb.com/igdb/image/upload/t_{size}/{image_id}.jpg"
    response = requests.get(url)
    return response.content


@task
def sync_igdb_coverart():
    """Downloads IGDB coverart and associates it with Lutris games"""
    cover_format = "cover_big"
    for igdb_cover in ProviderCover.objects.filter(provider__name="igdb"):
        relpath = f"{cover_format}/{igdb_cover.image_id}.jpg"
        igdb_path = os.path.join(settings.MEDIA_ROOT, "igdb", relpath)
        if os.path.exists(igdb_path):
            continue
        try:
            igdb_game = ProviderGame.objects.get(provider__name="igdb", slug=igdb_cover.game)
        except ProviderGame.DoesNotExist:
            LOGGER.warning("No IGDB game with ID %s", igdb_cover.game)
            continue
        try:
            lutris_game = Game.objects.get(provider_games=igdb_game)
        except Game.DoesNotExist:
            LOGGER.warning("No Lutris game with ID %s", igdb_cover.game)
            continue
        lutris_game.coverart = ContentFile(
            get_igdb_cover(igdb_cover.image_id),
            relpath
        )
        lutris_game.save()
        LOGGER.info("Saved cover for %s", lutris_game)


@task
def deduplicate_igdb_games():
    """IGDB uses a different slugify method,
    using dashes on apostrophes where we don't"""
    # Select all title with an apostrophe that don't have an IGDB game already
    games = Game.objects.filter(
        change_for__isnull=True,
        name__contains="'"
    ).exclude(provider_games__provider__name="igdb")
    for game in games:
        # Generate a new slug
        igdb_slug = slugify(game.name.replace("'", "-"))
        # print(game)
        # print(igdb_slug)
        # Check the presence of an IGDB game
        try:
            igdb_game = Game.objects.get(provider_games__provider__name="igdb", slug=igdb_slug)
        except Game.DoesNotExist:
            # No IGDB game found, just keep going
            continue
        game.merge_with_game(igdb_game)
