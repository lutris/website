"""Global provider task module, expose Celery tasks here."""
from providers.tasks.igdb import (
    load_igdb_games,
    load_igdb_genres,
    load_igdb_platforms,
    load_igdb_covers,
    match_igdb_games,
    sync_igdb_coverart,
    sync_igdb_platforms,
    deduplicate_igdb_games
)
from providers.tasks.gog import cache_gog_games
