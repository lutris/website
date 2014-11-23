import os
import hashlib
from optparse import make_option
from tosec.models import Rom, Game
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<folder>'
    help = 'Scan a folder for TOSEC roms'
    option_list = BaseCommand.option_list + (
        make_option('--destination', action='store', type="str"),
        make_option('--create-set-folders', action='store_true',
                    dest="create_set_folders"),

    )

    def handle(self, *args, **options):
        directory = args[0]
        dest = options.get('destination')
        if not dest:
            dest = os.path.join(directory, 'TOSEC')
        if not os.path.exists(dest):
            os.makedirs(dest)
        create_set_folders = options['create_set_folders']
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
            if create_set_folders:
                set_path = os.path.join(dest, set_name)
                if not os.path.exists(set_path):
                    os.mkdir(set_path)
                dest_path = os.path.join(set_path, rom.name)
            else:
                dest_path = os.path.join(dest, rom.name)
            os.rename(abspath, dest_path)

        for set_name in tosec_sets:
            set_size = Game.objects.filter(category__name=set_name).count()
            self.stdout.write("{}: imported {} of {} games".format(
                set_name, tosec_sets[set_name], set_size
            ))
