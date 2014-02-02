from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<tosec_catalog tosec_catalog ...>'
    help = "Import Tosec catalog files in the database"

    def handle(self, *args, **kwargs):
        for filename in args:
            self.stdout.write("Importing %s" % filename)
            self.stdout.write("TODO: write actual import")
