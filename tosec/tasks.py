"""TOSEC tasks"""
import os

from django.conf import settings

from tosec.utils import import_tosec_database


def import_tosec(folder='TOSEC'):
    """Import several TOSEC dat files to the database"""
    basepath = os.path.join(settings.TOSEC_DAT_PATH, folder)
    if not os.path.exists(basepath):
        print(f"No TOSEC database found in {basepath}")
        return
    filenames = [
        os.path.join(basepath, f)
        for f in os.listdir(basepath)
        if f.lower().endswith(".dat")
    ]
    total_files = len(filenames)
    for index, filename in enumerate(filenames, start=1):
        print(f"Importing {filename} [{index} of {total_files}]")
        import_tosec_database(filename)
