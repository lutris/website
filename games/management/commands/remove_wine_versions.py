"""Removes specified Wine versions from all installers."""
import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from common.util import load_yaml, dump_yaml
from games.models import Installer

LOGGER = logging.getLogger(__name__)

VERSIONS_TO_KEEP = (
    'tkg-mwo-4.1-x86_64',
    'tkg-osu-4.6-x86_64',
    'lutris-lol-4.20-x86_64',
    'lutris-mtga-4.21-x86_64',
    'lutris-fshack-5.0-rc2-x86_64',
    'lutris-vkchildwindow-5.0-rc2-x86_64'
)


class Command(BaseCommand):
    help = "Removes specified Wine versions from all installers."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help="don't write to the database"
        )

    @classmethod
    def remove_wine_version(cls, script, slug):
        # pylint: disable=too-many-return-statements
        wine_config = script.get("wine")
        if not wine_config:
            return False
        wine_version = wine_config.get("version")
        if not wine_version:
            return False
        if not cls.version_filter(wine_version):
            return False

        LOGGER.info("Removing Wine version %s from %s", wine_version, slug)
        del wine_config["version"]
        if not wine_config:
            del script["wine"]
        return True

    @staticmethod
    def version_filter(version):
        return version not in VERSIONS_TO_KEEP

    def handle(self, *args, **options):
        """Removes specified Wine versions from all installers."""
        dry_run = options.get('dry_run')

        # Search for installers that have a Wine version specified.
        installers = Installer.objects.filter(
            Q(content__contains="\nwine:")
            & Q(content__contains="  version: ")
        )
        for installer in installers:
            script = load_yaml(installer.content)
            changed = self.remove_wine_version(
                script,
                installer.slug,
            )
            if not changed:
                continue
            installer.content = dump_yaml(script)
            if dry_run:
                LOGGER.info("Not saving installer %s, dry run only", installer)
            else:
                LOGGER.info("Updating installer %s", installer)
                installer.save()
