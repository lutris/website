from django.core.management import call_command
from django.core.management import BaseCommand

from django.db import connection
from StringIO import StringIO


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # 'call' manage.py flush and capture its outputted sql
        command_output = StringIO()
        call_command("sqlflush", stdout=command_output)

        command_output.seek(0)
        flush_sql = command_output.read().strip()

        # execute the sql
        # from: https://docs.djangoproject.com/en/dev/topics/db/sql/#executing-custom-sql-directly
        cursor = connection.cursor()
        for statement in flush_sql:
            print(statement)
            print(type(statement))
            cursor.execute(statement)
        print("db has been reset")
