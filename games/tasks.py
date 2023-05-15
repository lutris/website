"""Celery tasks for account related jobs"""
from celery.utils.log import get_task_logger
from django.db.models import Q

from common.models import KeyValueStore
from games import models

from lutrisweb.celery import app
LOGGER = get_task_logger(__name__)


@app.task
def clean_action_log():
    """Remove zero value entries from log"""
    KeyValueStore.objects.filter(
        Q(key="spam_avatar_deleted")
        | Q(key="spam_website_deleted"),
        value=0
    ).delete()


@app.task
def populate_popularity():
    """Update the popularity field for all"""
    i = 0
    total_games = models.Game.objects.all().count()
    for game in models.Game.objects.all():
        i += 1
        if i % 10000 == 0:
            LOGGER.info("updated %s/%s games", i, total_games)
        library_count = game.libraries.all().count()
        # Only update games in libraries to speed up the process
        if library_count:
            game.popularity = library_count
            game.save(skip_precaching=True)
