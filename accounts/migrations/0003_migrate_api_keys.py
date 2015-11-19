# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def migrate_keys(apps, schema_editor):
    Token = apps.get_model("authtoken", "Token")
    ApiKey = apps.get_model("tastypie", "ApiKey")
    for key in ApiKey.objects.all():
        Token.objects.create(
            user=key.user,
            key=key.key,
            created=key.created
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20150717_2226'),
        ('tastypie', '0001_initial'),
        ('authtoken', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_keys),
    ]
