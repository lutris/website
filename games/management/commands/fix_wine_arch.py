"""Adds missing architectures to wine scripts"""
import logging
from django.core.management.base import BaseCommand

from common.util import load_yaml, dump_yaml
from games.models import Installer

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "My shiny new management command."

    def add_arch_to_non_wine_installers(self, installer):
        script_updated = False
        script = load_yaml(installer.content)
        for step in [step for step in script["installer"] if "task" in step]:
            task = step["task"]
            if task["name"] == "wine.wineexec" and "arch" not in task:
                step["task"]["arch"] = "win32"
                script_updated = True

        if script_updated:
            installer.content = dump_yaml(script)
        return script_updated

    def add_arch_to_wine_installers(self, installer):
        script_updated = False
        script = load_yaml(installer.content)
        try:
            game_config = script.get("game", {})
        except AttributeError:
            LOGGER.error("The script %s is invalid", installer.slug)
            return False

        # Intaller ahs arch, we're good
        if game_config.get("arch") in ("win32", "win64"):
            # Game has architecture already set
            return False
        if game_config.get("arch"):
            raise ValueError("Weird value for arch: %s", game_config["arch"])

        # Set a prefix so the game doesn't use ~/.wine
        if "prefix" not in game_config:
            LOGGER.warning("No prefix found for %s", installer.slug)
            detected_prefix = None
            for task in [
                step for step in script.get("installer", []) if "task" in step
            ]:
                if "prefix" in task:
                    if detected_prefix and detected_prefix != task["prefix"]:
                        raise ValueError("Different values of prefixes found")
                    detected_prefix = task["prefix"]
            if not detected_prefix:
                detected_prefix = "$GAMEDIR"
            LOGGER.info("Setting prefix to %s", detected_prefix)
            game_config["prefix"] = detected_prefix
            script_updated = True

        if "Program Files (x86)" in installer.content:
            LOGGER.info("%s is a 64bit game?", installer.slug)
            detected_arch = "win64"
        else:
            detected_arch = "win32"
        LOGGER.info("Setting arch for %s to %s", installer.slug, detected_arch)
        game_config["arch"] = detected_arch
        script_updated = True

        if script_updated:
            script["game"] = game_config
            installer.content = dump_yaml(script)
        return True

    def handle(self, *args, **options):
        """Change install scripts to specify wine prefix architecture"""
        installers = Installer.objects.filter(
            content__icontains="Program Files"
        )
        for installer in installers:
            if installer.runner.slug != "wine":
                script_updated = self.add_arch_to_non_wine_installers(
                    installer
                )
            else:
                script_updated = self.add_arch_to_wine_installers(installer)
            if script_updated:
                LOGGER.info("Updating installer %s", installer)
                installer.save()
