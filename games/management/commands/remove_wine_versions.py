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
            type=bool,
            dest='dry_run',
            help="don't write to the database"
        )
        '''
        parser.add_argument(
            '--all-except',
            action='store_true',
            type=bool,
            dest='all_except',
            help="remove all Wine versions except the specified"
        )
        parser.add_argument(
            '--force',
            action='store_true',
            type=bool,
            dest='force',
            help="run even without specified Wine versions "
                 "(dangerous with --all-except)"
        )
        parser.add_argument(
            'versions',
            action='append',
            nargs='+',
            type=list,
            dest='versions',
            help="the Wine versions to remove/keep"
        )
        '''

    @staticmethod
    def remove_wine_version(script, slug, version_filter):
        # pylint: disable=too-many-return-statements

        not_found = object()

        try:
            wine_config = script.get("wine", not_found)
            if wine_config is not_found:
                return False
        except AttributeError:
            LOGGER.error("The script %s is invalid", slug)
            return False

        try:
            wine_version = wine_config.get("version", not_found)
            if wine_version is not_found:
                return False
        except AttributeError:
            LOGGER.error("The script %s is invalid", slug)
            return False

        if not version_filter(wine_version):
            return False

        LOGGER.info("Removing Wine version %s from %s", wine_version, slug)
        try:
            del wine_config["version"]
            if not wine_config:
                del script["wine"]
        except TypeError:
            LOGGER.error("The script %s is invalid", slug)
            return False
        return True

    def handle(self, *args, **options):
        """Removes specified Wine versions from all installers."""

        # Get dry run flag from options.
        dry_run = options.get('dry_run')

        '''
        # Get the specified Wine versions from the command line.
        versions = options.get('versions')
        # If no versions were specified and --force not given,
        # refuse to run.
        if not versions and not options.get('force'):
            LOGGER.error("No versions specified, use --force to run anyway")
            return

        # Create version filter lambda from versions.
        if options.get('all_except'):
            version_filter = lambda version: version not in versions
        else:
            version_filter = lambda version: version in versions
        '''
        version_filter = lambda version: version not in VERSIONS_TO_KEEP

        # Search for installers that have a Wine version specified.
        installers = Installer.objects.filter(
            (  # JSON format
                Q(content__icontains=',"wine":{')
                & Q(content__icontains='"version":')
            ) | (  # YAML format
                Q(content__icontains=r"\nwine:\n  ")
                & Q(content__icontains=r"\n  version: ")
            )
        )
        # For each of those installers:
        for installer in installers:
            # Parse the installer content.
            script = load_yaml(installer.content)

            # Remove the Wine version if it's not in
            # the list of versions to keep.
            changed = Command.remove_wine_version(
                script,
                installer.slug,
                version_filter
            )
            # If the script hasn't been changed, there's
            # no need to save it.
            if not changed:
                continue

            # Serialize the new installer content.
            installer.content = dump_yaml(script)

            # Save the new installer in the database.
            LOGGER.info("Updating installer %s", installer)
            if not dry_run:
                installer.save()
