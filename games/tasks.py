"""Celery tasks for account related jobs"""
from collections import defaultdict
from celery import task
from celery.utils.log import get_task_logger
from django.db.models import Q

from common.models import KeyValueStore
from games import models

LOGGER = get_task_logger(__name__)



@task
def delete_unchanged_forks():
    """Periodically delete forked installers that haven't received any changes"""


@task
def clear_orphan_versions():
    """Deletes versions that are no longer associated with an installer"""


@task
def clear_orphan_revisions():
    """Clear revisions that are no longer attached to any object"""


@task
def clean_action_log():
    """Remove zero value entries from log"""
    KeyValueStore.objects.filter(
        Q(key="clear_orphan_versions")
        | Q(key="clear_orphan_revisions")
        | Q(key="delete_unchanged_forks")
        | Q(key="spam_avatar_deleted")
        | Q(key="spam_website_deleted"),
        value=0
    ).delete()


@task
def auto_process_installers():
    """Auto deletes or accepts some submissions"""


def process_new_steam_installers():
    """Auto publish Steam installers"""
    stats = defaultdict(int)
    for installer in models.Installer.objects.new():
        if installer.runner.slug != "steam":
            stats["non-steam"] += 1
            continue
        stats["steam"] += 1
        script = installer.raw_script
        if script == {'game': {'appid': installer.game.steamid}}:
            installer.published = True
            installer.save()
            stats["published"] += 1
        print(script)
        print(installer.game.provider_games.filter(provider__name="steam"))
    return stats


@task
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
