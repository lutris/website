import logging
from games.models import Game, Genre
from games.util.steam import get_store_info, create_steam_installer
from platforms.models import Platform
from providers.models import ProviderGame, Provider
from common.util import slugify

LOGGER = logging.getLogger(__name__)

def create_game_from_steam_appid(appid):
    store_info = get_store_info(appid)
    if not store_info:
        LOGGER.warning("No store info for game %s", appid)
        return
    if store_info["type"] != "game":
        LOGGER.warning("%s: %s is not a game (type: %s)",
                        appid, store_info["name"], store_info["type"])
        return
    steam_provider = Provider.objects.get(name="steam")
    provider_game = ProviderGame.objects.filter(provider=steam_provider, slug=appid)
    if provider_game.count():
        provider_game = provider_game[0]
    else:
        print(appid)
        provider_game = ProviderGame.objects.create(
            provider=steam_provider,
            slug=appid,
            internal_id=appid,
            name=store_info["name"],

        )
    slug = slugify(store_info["name"])
    existing_games = Game.objects.filter(slug=slug)
    if existing_games.count():
        for game in existing_games:
            game.add(provider_game)
        LOGGER.warning("Game %s already in Lutris but does not have a Steam ID (%s)", slug, appid)
        return

    game = Game.objects.create(
        name=store_info["name"],
        slug=slug,
        steamid=appid,
        description=store_info["short_description"],
        website=store_info["website"] or "",
        is_public=True,
    )
    game.set_logo_from_steam()
    LOGGER.debug("%s created", game)
    if store_info["platforms"]["linux"]:
        platform = Platform.objects.get(slug='linux')
        LOGGER.info("Creating installer for %s", game)
        create_steam_installer(game)
    else:
        platform = Platform.objects.get(slug='windows')
    game.platforms.add(platform)
    for steam_genre in store_info["genres"]:
        genre, created = Genre.objects.get_or_create(slug=slugify(steam_genre["description"]))
        if created:
            genre.name = steam_genre["description"]
            LOGGER.info("Created genre %s", genre.name)
            genre.save()
        game.genres.add(genre)


    game.provider_games.add(provider_game)
    game.save()
