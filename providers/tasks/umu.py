"""Compare GOG games to the Lutris library"""

from celery.utils.log import get_task_logger

from providers.umu import (
    update_repository,
    import_umu_games,
    check_lutris_associations,
    save_umu_games,
)
from common.models import save_action_log
from lutrisweb.celery import app
from games.webhooks import send_simple_message

LOGGER = get_task_logger(__name__)


@app.task
def update_umu_games():
    """Task to load GOG games from the API"""
    update_repository()
    check_lutris_associations()
    stats = import_umu_games()
    save_umu_games()
    save_action_log("update_protonfixes", stats)
    send_simple_message("umu games loaded: %s" % stats)
