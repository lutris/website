"""Celery tasks for account related jobs"""
from celery.utils.log import get_task_logger
from celery import task
from reversion.models import Version, Revision
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from games import models
from common.models import KeyValueStore

LOGGER = get_task_logger(__name__)

def save_action_log(key, value):
    """Save the results of a task as a KeyValueStore object"""
    log_object,_created = KeyValueStore.objects.create(key=key)
    log_object.value = str(value)
    log_object.save()


@task
def delete_unchanged_forks():
    """Periodically delete forked installers that haven't received any changes"""
    installers_deleted = 0
    for installer in models.Installer.objects.abandoned():
        installer.delete()
        installers_deleted += 1
    save_action_log("delete_unchanged_forks", installers_deleted)


@task
def clear_orphan_versions():
    """Deletes versions that are no longer associated with an installer"""
    content_type = ContentType.objects.get_for_model(models.Installer)
    versions_deleted = 0
    for version in Version.objects.filter(content_type=content_type):
        if version.object:
            continue
        LOGGER.warning("Deleting orphan version %s", version)
        version.delete()
        versions_deleted += 1
    save_action_log("clear_orphan_versions", versions_deleted)


@task
def clear_orphan_revisions():
    """Clear revisions that are no longer attached to any object"""
    result = Revision.objects.filter(version__isnull=True).delete()
    save_action_log("clear_orphan_revisions", result)




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
    """Shorten installer description by removing some data"""
    description_removals = [
        "This script will facilitate you install of this game on Linux OS:",
        "This script will assist you to install this game on Linux OS:",
        "This script will facilitate install of this app on Linux OS:",
        "This script facilitates you install of this game on Linux OS:",
        "This script will facilitate install install of this game on Linux OS:",
        "This script will assit you to install this gae on Linux OS:",
        "This script will assist you to install this game on Linux OS:",
        "This script will assit you to install this game on Linux OS:",
        "This script will facilitate you to install of this game:",
        "This script will facilitate install of this game on Linux OS:",
        "This script will facilitate you to install of this game on Linux OS:",
        "This script will facilitate you install on this game on Linux OS:",
        "This Lutris script installer will facilitate install of this game on Linux OS:",
        "This script will install ",
        "This script will assist you to install ",
        "This script will facilitate you install ",
        " provided by GOG",
        " provided by Steam.",
        " using Lutris Wine runner",
        " using ScummVM Lutris runner",
        " using ScummVM runner.",
        "This script will facilitate you install of ",
        "This script facilitates the installation of the ",
        "During install please let all options by default.",
        "During install, please let all options by default.",
        "During installation please let all options stay default.",
        "Big thanks to the people who helped us play this game in the best conditions on Linux.",
        "Big thanks to the people who helped us play this game in the best conditions on Linux platform.",
        "Big thanks to people who gave their time to permit us using this application in the best conditions on Linux platform.",
        "Big thanks to people who gave their time to permit us playing this game in the best conditions on Linux platform.",
        "Big thanks to people who gave their time to permit us playing this game in the best conditions on Linux.",
        "Big thanks to people who gave their time to permit us playing this game in the best conditions.",
        "Big thanks to people who gave their time to permit using this application in the best conditions on Linux."
        "Big thanks to the people who contributed to play this game in the best conditions on Linux.",
        "Big thanks to people who helped us play this game in the best conditions on Linux.",
        "A big thank you to the people who help to play this game in the best conditions on Linux.",
        "Many thanks to the people who helped us to play this game in the best conditions on Linux platform.",
        "Many thanks to the people who helped us to play this game in the best conditions on Linux.",
        "Many thanks to the people who helped us to play this game in the best conditions.",

        "Thanks to the people who contributed to play this game in the best conditions on Linux platform.",
        "Thanks to the people who contribute to play this game in the best conditions on Linux platform.",
        "Thanks to the people who helped us playing this game in the best conditions on Linux platform.",
        "Thanks to the people who helped us play this game in the best conditions on Linux platform.",
        "Thanks to the people who contributed to play this game in the best conditions on Linux.",
        "Thanks to the people who helped us playing this game in the best conditions on Linux.",
        "Thanks to the people who helped us play this game in the best conditions on Linux.",
        "Thanks to the people who contributed to play this game in the best conditions.",
        "Thanks to the people who helped us play this game in the best conditions.",
        "Uses the files from the Windows installer from GOG."
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
        Q(description__icontains="this script") |
        Q(description__icontains="facilitate") |
        Q(description__icontains="best conditions") |
        Q(description__icontains="uses the files") |
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
