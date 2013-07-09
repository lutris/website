from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from tastypie.models import ApiKey


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        users = User.objects.all()

        for user in users:
            try:
                user.api_key
            except ObjectDoesNotExist:
                self.stdout.write("Creating api key for %s" % str(user))
                ApiKey.objects.create(user=user)
