from pprint import pprint
from tosec import models
from tosec.parser import TosecParser
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<tosec_catalog tosec_catalog ...>'
    help = "Import Tosec catalog files in the database"

    def handle(self, *args, **kwargs):
        for filename in args:
            self.stdout.write("Importing %s" % filename)
            with open(filename, 'r') as tosec_dat:
                dat_contents = tosec_dat.readlines()

            tosec_parser = TosecParser(dat_contents)
            tosec_parser.parse()

            category = models.Category(
                name=tosec_parser.headers['name'],
                description=tosec_parser.headers['description'],
                category=tosec_parser.headers['category'],
                version=tosec_parser.headers['version'],
                author=tosec_parser.headers['author'],
            )
            category.save()

            for game in tosec_parser.games:
                game_row = models.Game(
                    category=category,
                    name=game['name'],
                    description=game['description'],
                )
                game_row.save()
                rom = game['rom']
                rom_row = models.Rom(
                    game=game_row,
                    name=rom['name'],
                    size=rom['size'],
                    crc=rom['crc'],
                    md5=rom['md5'],
                    sha1=rom['sha1'],
                )
                rom_row.save()
