""" Compare GOG games to the Lutris library """
import os
from celery import task
from celery.utils.log import get_task_logger
from django.conf import settings

from providers.gog import load_games_from_gogdb, match_from_gogdb
from common.models import save_action_log


LOGGER = get_task_logger(__name__)


@task
def load_gog_games():
    """Task to load GOG games from a GOGDB dump"""
    file_path = os.path.join(settings.GOG_CACHE_PATH, "gogdb.json")
    if not os.path.exists(file_path):
        LOGGER.error("No file present at %s", file_path)
        return None
    stats = load_games_from_gogdb(file_path)
    save_action_log("load_gog_games", stats)
    return stats


@task
def match_gog_games():
    """Match GOG games with Lutris games"""
    stats = match_from_gogdb(create_missing=True)
    save_action_log("match_gog_games", stats)
    return stats
