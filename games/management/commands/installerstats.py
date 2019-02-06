from django.core.management.base import BaseCommand
from common.util import load_yaml
from games import models


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write("Installer stats\n")
        installers = models.Installer.objects.all()
        command_stats = {}
        for installer in installers:
            slug = installer.slug
            installer_content = load_yaml(installer.content)
            commands = installer_content.get("installer", [])
            for command in commands:
                command_key = command.keys()[0]
                if command_key not in command_stats:
                    command_stats[command_key] = set()
                command_stats[command_key].add(installer.slug)

        for command in command_stats:
            self.stdout.write(command)
            for slug in command_stats[command]:
                self.stdout.write("\t" + slug)
