"""Global provider task module, expose Celery tasks here."""
from providers.tasks.gog import load_gog_games, match_gog_games
from providers.tasks.igdb import (deduplicate_igdb_games, load_igdb_covers,
                                  load_igdb_games, load_igdb_genres,
                                  load_igdb_platforms, match_igdb_games,
                                  sync_igdb_coverart, sync_igdb_platforms)
from providers.tasks.steam import load_steam_games
