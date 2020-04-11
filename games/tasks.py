"""Celery tasks for account related jobs"""
import logging

import requests
from django.conf import settings
from reversion.models import Version, Revision
from django.contrib.contenttypes.models import ContentType
from games import models
from lutrisweb import celery_app

LOGGER = logging.getLogger(__name__)


@celery_app.task
def delete_unchanged_forks():
    """Periodically delete forked installers that haven't received any changes"""
    for installer in models.Installer.objects.abandoned():
        installer.delete()


@celery_app.task
def clear_orphan_versions():
    """Deletes versions that are no longer associated with an installer"""
    content_type = ContentType.objects.get_for_model(models.Installer)
    for version in Version.objects.filter(content_type=content_type):
        if version.object:
            continue
        LOGGER.warning("Deleting orphan version %s", version)
        version.delete()


@celery_app.task
def clear_orphan_revisions():
    """Clear revisions that are no longer attached to any object"""
    Revision.objects.filter(version__isnull=True).delete()


@celery_app.task
def add_new_games():
    """Check MobyGames for newly added games every 3 hours and update Lutris DB"""
    #
    response = requests.get(url="https://api.mobygames.com/v1/games/recent",
                            params={
                                'api_key': settings.MOBY_API_KEY,
                                'format': 'normal',
                                'age': 1
                            })
    if response.status_code == 200:
        new_entries = 0
        data = response.json()
        supported_platforms = models.Platform.objects.values_list('name', flat=True)
        supported_genres = models.Genre.objects.values_list('name', flat=True)
        for game in data.get('games', []):
            game_platforms = [platform.get('platform_name', '') for platform in game.get('platforms', [])
                              if platform.get('platform_name', '') in supported_platforms]
            game_genres = [genre.get('genre_name', '') for genre in game.get('genres', [])
                           if genre.get('genre_name', '') in supported_genres]
            if game_platforms:
                obj, created = models.Game.objects.get_or_create(
                    name=game.get('title', ''),
                    defaults={
                        'description': game.get('description', '')
                    }
                )
                if created:
                    new_entries += 1
                    obj.platforms.add(*models.Platform.objects.filter(name__in=game_platforms))
                    obj.genres.add(*models.Genre.objects.filter(name__in=game_genres))
    else:
        pass
