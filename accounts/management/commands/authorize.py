from django.core.management.base import BaseCommand
from mithril.models import Whitelist


class Command(BaseCommand):
    args = '<ip>'
    help = 'Authorize IP for private beta.'

    def handle(self, *args, **options):
        ip_address = args[0]
        whitelist = 'devel'

        try:
            beta_whitelist = Whitelist.objects.get(slug=whitelist)
        except Whitelist.DoesNotExist:
            self.stderr.write('Cant find whitelist %s\n' % whitelist)
            return

        beta_whitelist.range_set.create(ip=ip_address, cidr=32)
        self.stdout.write('Successfully authorized ip  "%s"\n' % ip_address)
