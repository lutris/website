from celery import task

from games import models


@task
def delete_unchanged_forks():
    """Periodically delete forked installers that haven't received any changes"""
    for installer in models.Installer.objects.abandoned():
        installer.delete()
