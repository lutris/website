import logging

from django.core.management.base import BaseCommand
from reversion.models import Revision
from games.models import InstallerRevision


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        revisions = Revision.objects.all()
        # filter(comment__startswith="[submission]")
        for revision in revisions:
            version = revision.version_set.first()
            submission = InstallerRevision(version)
            original = version.object
            if submission.content != original.content:
                # Content change needs manual review
                continue

            if submission.runner != original.runner:
                if submission.runner.slug == "steam" and original.runner.slug == "winesteam":
                    LOGGER.info("Accepting %s (%s > %s)", submission, original.runner, submission.runner)
                    # submission.accept()
                    continue
                LOGGER.info("Rejecting %s (%s > %s)", submission, original.runner, submission.runner)
                # submission.delete()