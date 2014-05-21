import os
import hashlib
from tosec.models import Rom
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<folder>'
    help = 'Scan a folder for TOSEC roms'

    def handle(self, *args, **kwargs):
        directory = args[0]
        dest = os.path.join(directory, 'TOSEC')
        if not os.path.exists(dest):
            os.makedirs(dest)
        self.stdout.write("Scanning %s" % directory)
        for filename in os.listdir(directory):
            abspath = os.path.join(directory, filename)
            if not os.path.isfile(abspath):
                continue
            md5sum = hashlib.md5(open(abspath).read()).hexdigest()
            rom = Rom.objects.filter(md5=md5sum)
            if not rom:
                continue
            else:
                rom = rom[0]

            self.stdout.write("Found %s" % rom.name)
            new_path = os.path.join(dest, rom.name)
            os.rename(abspath, new_path)
