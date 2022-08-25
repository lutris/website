import json
from collections import defaultdict

from django.core.management.base import BaseCommand
from common.util import load_yaml
from games import models


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write("Installer stats\n")
        installers = models.Installer.objects.all()
        url_stats = defaultdict(list)
        for installer in installers:
            slug = installer.slug
            installer_content = load_yaml(installer.content)
            try:
                files = installer_content.get("files", [])
            except AttributeError:
                print("Deleting installer %s" % installer)
                installer.delete()
                continue
            if files is None:
                print("Deleting installer %s" % installer)
                installer.delete()
                continue
            for url_dict in files:
                fileid = next(iter(url_dict))
                try:
                    url = url_dict[fileid]
                except TypeError:
                    print("Deleting installer %s" % installer)
                    installer.delete()
                    continue
                if isinstance(url, str):
                    if url.startswith("N/A"):
                        continue
                    url_stats[url].append(slug)
                elif isinstance(url, dict):
                    if url["url"].startswith("N/A"):
                        continue
                    url_stats[url["url"]].append(slug)

        with open("installer-files.json", "w") as installer_files:
            json.dump(url_stats, installer_files, indent=2)
