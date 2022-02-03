"""Celery tasks for account related jobs"""
from celery.utils.log import get_task_logger
from celery import task
from reversion.models import Version, Revision
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from games import models

LOGGER = get_task_logger(__name__)


@task
def delete_unchanged_forks():
    """Periodically delete forked installers that haven't received any changes"""
    for installer in models.Installer.objects.abandoned():
        installer.delete()


@task
def clear_orphan_versions():
    """Deletes versions that are no longer associated with an installer"""
    content_type = ContentType.objects.get_for_model(models.Installer)
    for version in Version.objects.filter(content_type=content_type):
        if version.object:
            continue
        LOGGER.warning("Deleting orphan version %s", version)
        version.delete()


@task
def clear_orphan_revisions():
    """Clear revisions that are no longer attached to any object"""
    Revision.objects.filter(version__isnull=True).delete()


@task
def auto_process_installers():
    """Auto deletes or accepts some submissions"""
    revisions = Revision.objects.all()
    for revision in revisions:
        version = revision.version_set.first()
        if not version:
            continue
        try:
            submission = models.InstallerRevision(version)
        except Exception as ex:  # pylint: disable=broad-except
            LOGGER.error("Deleting corrupt submission %s: %s", version, ex)
            submission.delete()
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
        if not original.description:
            original.description = ""
        if (
                submission.description.strip() == original.description.strip()
                and submission.notes.strip() == original.notes.strip()
        ):
            LOGGER.info("No change in submission, deleting %s", submission)
            submission.delete()
            continue

        if "[draft]" in revision.comment:
            LOGGER.info("Deleting draft  with only meta changes %s", submission)
            submission.delete()
            continue

        if original.version == "Change Me":
            LOGGER.info("Deleting garbage fork %s", submission)
            submission.delete()
            continue


@task
def cleanup_installers():

    description_removals = [
        "This script will facilitate you install of this game on Linux OS:",
        "This script will install",
        "During install please let all options by default.",
        "Big thanks to people who gave their time to permit us playing this game in the best conditions on Linux platform.",
        "Thanks to the people who helped us play this game in the best conditions on Linux platform.",
        "Thanks to the people who contribute to play this game in the best conditions on Linux platform.",
        "Thanks to the people who helped us play this game in the best conditions."
    ]


    notes_removal = [
        "- x360 gamepad compatible",
        "- x360 controller compatible",
        "- x360 compatible",
        "- Known issues:",
        "- Known issue:",
        "- Knowns issues:",
        "- Please report issue concerning this script on my Github page:",
        "- Please report issue concerning this script on my github page:",
        "https://github.com/legluondunet/MyLittleLutrisScripts/",
        "https://github.com/legluondunet/MyLittleLutrisScripts",
    ]


    for installer in models.Installer.objects.filter(
        Q(description__contains="facilitate") |
        Q(description__contains="best conditions") |
        Q(notes__icontains="x360") |
        Q(notes__icontains="legluondunet") |
        Q(notes__icontains="issue")
    ):
        print(installer)
        if not installer.description:
            installer.description = ""
        for removal in description_removals:
            installer.description = installer.description.replace(removal, "")
        installer.description = installer.description.strip()

        if not installer.notes:
            installer.notes = ""
        for removal in notes_removal:
            installer.notes = installer.notes.replace(removal, "")
        installer.notes = installer.notes.strip()

        installer.save()
