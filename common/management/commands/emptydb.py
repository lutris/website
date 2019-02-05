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
        print flush_sql
        flush_sql = """DELETE FROM "auth_permission";
DELETE FROM "auth_group";
DELETE FROM "django_site";
DELETE FROM "accounts_user_user_permissions";
DELETE FROM "django_content_type";
DELETE FROM "django_session";
DELETE FROM "accounts_user";
DELETE FROM "django_openid_auth_useropenid";
DELETE FROM "django_admin_log";
DELETE FROM "auth_group_permissions";
DELETE FROM "django_openid_auth_nonce";
DELETE FROM "news";
DELETE FROM "thumbnail_kvstore";
DELETE FROM "django_select2_keymap";
DELETE FROM "django_openid_auth_association";
DELETE FROM "south_migrationhistory";
DELETE FROM "accounts_user_groups";
DELETE FROM "common_upload";""".split('\n')

        # execute the sql
        # from: https://docs.djangoproject.com/en/dev/topics/db/sql/#executing-custom-sql-directly
        cursor = connection.cursor()
        for statement in flush_sql:
            print statement
            print type(statement)
            cursor.execute(statement)

        print "db has been reset"
