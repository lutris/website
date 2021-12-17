"""Provider tasks"""
import logging
from celery import task
from providers.gog import cache_gog_games

LOGGER = logging.getLogger(__name__)

@task
def refresh_cache():
    """Reload the local GOG cache"""
    cache_gog_games()
