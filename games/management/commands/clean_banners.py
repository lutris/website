"""Find and remove invalid game banners (0 bytes or HTML error pages)"""

import os
from django.conf import settings
from django.core.management.base import BaseCommand
from games.models import Game


class Command(BaseCommand):
    """Remove invalid banner files and clear the title_logo field"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report invalid banners without deleting them",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        invalid_count = 0

        for game in Game.objects.exclude(title_logo=""):
            if not game.title_logo.name:
                continue

            file_path = os.path.join(settings.MEDIA_ROOT, game.title_logo.name)

            if not os.path.exists(file_path):
                self.stdout.write(f"[missing] {game.slug} (id={game.id}): {game.title_logo.name}")
                if not dry_run:
                    game.title_logo = ""
                    game.save(update_fields=["title_logo"])
                invalid_count += 1
                continue

            file_size = os.path.getsize(file_path)
            if file_size == 0:
                self.stdout.write(f"[empty] {game.slug} (id={game.id}): {game.title_logo.name}")
                if not dry_run:
                    os.remove(file_path)
                    game.title_logo = ""
                    game.save(update_fields=["title_logo"])
                invalid_count += 1
                continue

            # Check if file is HTML (likely a 404 error page saved as image)
            with open(file_path, "rb") as f:
                header = f.read(256)
            if b"<html" in header.lower() or b"<!doctype" in header.lower():
                self.stdout.write(f"[html] {game.slug} (id={game.id}): {game.title_logo.name}")
                if not dry_run:
                    os.remove(file_path)
                    game.title_logo = ""
                    game.save(update_fields=["title_logo"])
                invalid_count += 1
                continue

        action = "Found" if dry_run else "Cleaned"
        self.stdout.write(self.style.SUCCESS(f"{action} {invalid_count} invalid banners"))
