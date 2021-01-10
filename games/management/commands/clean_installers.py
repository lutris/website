import logging

from django.core.management.base import BaseCommand
from reversion.models import Revision
from games.models import InstallerRevision, Installer


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """Auto rejects or accepts some installer submissions"""

    def handle(self, *args, **_kwargs):
        # Delete abandoned forks
        for installer in Installer.objects.abandoned():
            LOGGER.info("Deleting fork %s", installer)
            installer.delete()

        revisions = Revision.objects.all()
        # filter(comment__startswith="[submission]")
        for revision in revisions:
            version = revision.version_set.first()
            if not version:
                continue
            try:
                submission = InstallerRevision(version)
            except Exception:  # pylint: disable=broad-except
                LOGGER.error("%s is corrupt and should be deleted", version)
                continue
            original = version.object
            if submission.content != original.content:
                # Content change needs manual review
                continue

            if submission.runner != original.runner:
                if submission.runner.slug == "steam" and original.runner.slug == "winesteam":
                    LOGGER.info("Accepting %s (%s > %s)",
                                submission, original.runner, submission.runner)
                    submission.accept()
                    continue
                LOGGER.info("Rejecting %s (%s > %s)",
                            submission, original.runner, submission.runner)
                submission.delete()
                continue
            if (
                submission.description == original.description
                and submission.notes == original.notes
                and submission.version == original.version
            ):
                LOGGER.info("No change in submission, deleting %s", submission)
                submission.delete()

            LOGGER.info("!!! %s", submission)
