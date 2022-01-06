""" Compare GOG games to the Lutris library """
from datetime import datetime, timedelta

from celery import task
from celery.utils.log import get_task_logger
from django.db.models import Q
from django.db import IntegrityError
from django.utils import timezone

from games.models import Game, Genre
from platforms.models import Platform
from common.util import get_auto_increment_slug, slugify
from providers.gog import iter_gog_games, clean_gog_slug, clean_name, cache_gog_games
from providers.models import ProviderGame, Provider


LOGGER = get_task_logger(__name__)


def iter_lutris_games_by_gog_slug():
    """Iterate through Lutris games that have a valid GOG slug"""
    for gog_game in iter_gog_games():
        for game in Game.objects.filter(gogslug=gog_game["slug"]):
            yield (game, gog_game)


def iter_orphan_gog_games():
    """Iterate over GOG games that have no associated Lutris game"""
    for gog_game in iter_gog_games():
        if gog_game["type"] != 1:
            # Exclude special editions and DLCs
            continue
        if not Game.objects.filter(gogid=gog_game["id"]).count():
            yield gog_game

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

@task
def run_cache_gog_games():
    """Locally cache all GOG games as a background task"""
    cache_gog_games()

def sync_all_gog_games():
    """Read cached GOG files and matches the games against Lutris games"""

    sync_slugs_with_ids()

    # CAUTION! This can cause some mismatchs
    # sync_ids_by_slug()

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


@task
def load_gog_games():
    """Load GOG games from the local cache to provider games"""
    provider = Provider.objects.get(name="gog")
    for game in iter_gog_games():
        gog_game, created = ProviderGame.objects.get_or_create(provider=provider, slug=game["id"])
        gog_game.name = game["title"]
        gog_game.provider = provider
        gog_game.metadata = game
        gog_game.save()
        if created:
            LOGGER.info("Created new provider game %s", game["title"])


@task
def match_gog_games():
    """Match GOG games with Lutris games"""
    for provider_game in ProviderGame.objects.filter(provider__name="gog"):
        if "type" not in provider_game.metadata:
            print(provider_game.metadata)
            provider_game.delete()
            continue
        if provider_game.games.count() or provider_game.metadata["type"] != 1:
            # Game has been matched already or is not a game
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
        lutris_game.provider_games.add(provider_game)
