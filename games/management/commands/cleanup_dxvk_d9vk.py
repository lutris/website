"""Enables DXVK where D9VK was active before and removes
all D9VK attributes and dxvk_version from installers."""
import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from common.util import load_yaml, dump_yaml
from games.models import Installer

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command to remove d9vk from scripts"""
    help = ("Enables DXVK where D9VK was active before and removes "
            "all D9VK attributes and dxvk_version from installers.")

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help="don't write to the database"
        )

    @staticmethod
    def clean_up_dxvk_d9vk(script, slug):
        try:
            wine_config = script.get("wine") or script.get("winesteam")
            if not wine_config:
                return False
        except AttributeError:
            LOGGER.error("The script %s is invalid", slug)
            return False

        try:
            d9vk_version = wine_config.get("d9vk_version")
            dxvk_version = wine_config.get("dxvk_version")
        except AttributeError:
            LOGGER.error("The script %s is invalid", slug)
            return False

        changed = False

        if d9vk_version:
            LOGGER.info("Removing D9VK version %s from %s", d9vk_version, slug)
            del wine_config["d9vk_version"]
            changed = True
        if dxvk_version:
            LOGGER.info("Removing DXVK version %s from %s", dxvk_version, slug)
            del wine_config["dxvk_version"]
            changed = True

        try:
            d9vk = wine_config.get("d9vk")
            if not d9vk:
                return changed
            dxvk = wine_config.get("dxvk")
        except AttributeError:
            LOGGER.error("The script %s is invalid", slug)
            return changed

        if not dxvk:
            LOGGER.info(
                "Changing DXVK from %s to %s on %s",
                dxvk if dxvk else "nothing",
                d9vk,
                slug
            )
            wine_config["dxvk"] = d9vk

        LOGGER.info("Removing D9VK from %s", slug)
        del wine_config["d9vk"]
        if not wine_config:
            LOGGER.info("Removing wine section from %s", slug)
            script.pop("wine", None)
            script.pop("winesteam", None)
        return True

    def handle(self, *args, **options):
        """Enables DXVK where D9VK was active before and removes
        all D9VK attributes and dxvk_version from installers."""

        dry_run = options.get('dry_run')

        installers = Installer.objects.filter(
            Q(content__icontains="d9vk")
            | Q(content__icontains="dxvk_version")
        )
        for installer in installers:
            script = load_yaml(installer.content)
            changed = Command.clean_up_dxvk_d9vk(script, installer.slug)
            if not changed:
                continue
            installer.content = dump_yaml(script)
            if dry_run:
                LOGGER.info("Dry run only, not saving installer %s", installer)
            else:
                LOGGER.info("Saving installer %s", installer)
                installer.save()
