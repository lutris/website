import os
import hashlib
from tosec.models import Rom, Game
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
        filenames = os.listdir(directory)
        total_files = len(filenames)
        tosec_sets = {}  # Store TOSEC sets with number of found roms
        for index, filename in enumerate(filenames, start=1):
            abspath = os.path.join(directory, filename)
            if not os.path.isfile(abspath):
                continue
            md5sum = hashlib.md5(open(abspath).read()).hexdigest()
            try:
                rom = Rom.objects.get(md5=md5sum)
            except Rom.DoesNotExist:
                continue
            set_name = rom.game.category.name
            if set_name in tosec_sets:
                tosec_sets[set_name] += 1
            else:
                tosec_sets[set_name] = 1
            self.stdout.write("[{} of {}] Found {}".format(index,
                                                           total_files,
                                                           rom.name))
            new_path = os.path.join(dest, rom.name)
            os.rename(abspath, new_path)

        for set_name in tosec_sets:
            set_size = Game.objects.filter(category__name=set_name).count()
            self.stdout.write("{}: imported {} of {} games".format(
                set_name, tosec_sets[set_name], set_size
            ))
