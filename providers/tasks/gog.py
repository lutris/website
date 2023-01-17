""" Compare GOG games to the Lutris library """
from celery import task
from celery.utils.log import get_task_logger

from providers.gog import cache_gog_games, match_from_gog_api, load_games_from_gog_api, populate_gogid_and_gogslug
from common.models import save_action_log


LOGGER = get_task_logger(__name__)


@task
def load_gog_games():
    """Task to load GOG games from the API"""
    cache_gog_games()
    stats = load_games_from_gog_api()
    save_action_log("load_gog_games", stats)
    return stats


@task
def match_gog_games():
    """Match GOG games with Lutris games"""
    stats = match_from_gog_api()
    save_action_log("match_gog_games", stats)
    stats = populate_gogid_and_gogslug()
    save_action_log("populate_gogid_and_gogslug", stats)
    return stats
