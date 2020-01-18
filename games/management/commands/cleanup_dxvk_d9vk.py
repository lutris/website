"""Enables DXVK where D9VK was active before and removes
all D9VK attributes and dxvk_version from installers."""
import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from common.util import load_yaml, dump_yaml
from games.models import Installer

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ("Enables DXVK where D9VK was active before and removes "
            "all D9VK attributes and dxvk_version from installers.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            type=bool,
            dest='dry_run',
            help="don't write to the database"
        )

    @staticmethod
    def clean_up_dxvk_d9vk(script, slug):
        not_found = object()

        try:
            wine_config = script.get("wine", not_found)
            if wine_config is not_found:
                return False
        except AttributeError:
            LOGGER.error("The script %s is invalid", slug)
            return False

        try:
            d9vk_version = wine_config.get("d9vk_version", not_found)
            dxvk_version = wine_config.get("dxvk_version", not_found)
        except AttributeError:
            LOGGER.error("The script %s is invalid", slug)
            return False

        changed = False

        if d9vk_version is not not_found:
            LOGGER.info("Removing D9VK version %s from %s", d9vk_version, slug)
            del wine_config["d9vk_version"]
            changed = True
        if dxvk_version is not not_found:
            LOGGER.info("Removing DXVK version %s from %s", dxvk_version, slug)
            del wine_config["dxvk_version"]
            changed = True

        try:
            d9vk = wine_config.get("d9vk", not_found)
            if d9vk is not_found:
                return changed
            dxvk = wine_config.get("dxvk", not_found)
        except AttributeError:
            LOGGER.error("The script %s is invalid", slug)
            return changed

        if dxvk is not_found or not dxvk:
            LOGGER.info(
                "Changing DXVK from %s to %s on %s",
                dxvk if dxvk is not not_found else "<undefined>",
                d9vk,
                slug
            )
            wine_config["dxvk"] = d9vk

        LOGGER.info("Removing D9VK from %s", slug)
        del wine_config["d9vk"]
        return True

    def handle(self, *args, **options):
        """Enables DXVK where D9VK was active before and removes
        all D9VK attributes and dxvk_version from installers."""

        # Get dry run flag from options.
        dry_run = options.get('dry_run')

        # Search for installers that have a "d9vk", "d9vk_version", or
        # "dxvk_version" field specified.
        installers = Installer.objects.filter(
            (  # JSON format
                Q(content__icontains=',"wine":{')
                & (
                    Q(content__icontains='"d9vk":')
                    | Q(content__icontains='"d9vk_version":')
                    | Q(content__icontains='"dxvk_version":')
                )
            ) | (  # YAML format
                Q(content__icontains=r"\nwine:\n  ")
                & (
                    Q(content__icontains=r"\n  d9vk: ")
                    | Q(content__icontains=r"\n  d9vk_version: ")
                    | Q(content__icontains=r"\n  dxvk_version: ")
                )
            )
        )
        # For each of those installers:
        for installer in installers:
            # Parse the installer content.
            script = load_yaml(installer.content)

            # Run the clean up function on the script.
            changed = Command.clean_up_dxvk_d9vk(script, installer.slug)
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
