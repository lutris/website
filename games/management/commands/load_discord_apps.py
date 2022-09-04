from argparse import ArgumentParser
import json

from django.core.management.base import BaseCommand, CommandError

from games.models import Game


class Command(BaseCommand):
    updated_count: int = 0

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            'file',
            help="JSON File with game identifier and discord app ids"
        )

    def handle(self, *args, **options):
        with open(options['file'], 'r') as json_file:
            discord_app_list: list = json.load(json_file)
            if type(discord_app_list) is not list:
                raise CommandError("Invalid JSON Data, a list must be provided")

        for discord_app in discord_app_list:
            # Skip if required keys are missing
            if 'game' not in discord_app or 'discord_id' not in discord_app:
                self.stderr.write(f"Invalid Entry on JSON File {discord_app}")
                continue

            self.import_discord_app(discord_app['game'], discord_app['discord_id'])

        self.stdout.write(self.style.SUCCESS(f"Script Completed. Updated {self.updated_count} Games"))

    def import_discord_app(self, game: str, discord_id: str):
        """
        Add a Discord ID to a Game identified by a SLUG
        """

        qs = Game.objects.filter(slug=game)
        # Return if we don't have that game in our database
        if not qs.exists():
            self.stderr.write(f"Game Not Found {game}")
            return
        # Get the game object
        game = qs.get()
        # Skip known ids
        if game.discord_id == discord_id:
            self.stdout.write(self.style.INFO(f"Skipping Known ID for {game}"))
            return
        # Update and save
        game.discord_id = discord_id
        game.save()
        self.updated_count += 1
