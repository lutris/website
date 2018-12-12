"""Import a TOSEC database to the local database"""
import os
from django.conf import settings
from django.core.management.base import BaseCommand

from tosec.utils import import_tosec_database


class Command(BaseCommand):
    """Import a TOSEC dump to the Lutris database"""
    args = '<tosec_catalog tosec_catalog ...>'
    help = "Import Tosec catalog files in the database"

    def handle(self, *args, **_options):
        if args:
            filenames = args
        else:
            basepath = os.path.join(settings.TOSEC_DAT_PATH, 'TOSEC')
            if not os.path.exists(basepath):
                self.stderr.write("No TOSEC database found in %s" % basepath)
                return
            filenames = [os.path.join(basepath, f)
                         for f in os.listdir(basepath)]
        total_files = len(filenames)
        for index, filename in enumerate(filenames, start=1):
            self.stdout.write("Importing {} [{} of {}]".format(filename,
                                                               index,
                                                               total_files))
            import_tosec_database(filename)
