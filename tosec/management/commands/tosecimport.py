from pprint import pprint
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

            for game in tosec_parser.games:
                pprint(game)
