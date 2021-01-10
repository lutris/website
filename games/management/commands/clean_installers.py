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
            if not original:
                LOGGER.warning("Could not find original, deleting %s", submission)
                submission.delete()
                continue
            if submission.content.strip() != original.content.strip():
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
            if not submission.description:
                submission.description = ""
            if (
                str(submission.description) == str(original.description)
                and submission.notes.strip() == original.notes.strip()
                and submission.version.strip() == original.version.strip()
            ):
                LOGGER.info("No change in submission, deleting %s", submission)
                submission.delete()
                continue

            if original.version == "Change Me":
                LOGGER.info("Deleting garbage fork %s", submission)
                submission.delete()
                continue

            LOGGER.info("-- %s for %s --", submission, submission.game)
            LOGGER.info("'%s' > '%s'", original.description, submission.description)
            LOGGER.info("'%s' > '%s'", original.notes, submission.notes)
            LOGGER.info("'%s' > '%s'", original.version, submission.version)
