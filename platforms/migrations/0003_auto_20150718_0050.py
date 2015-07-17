# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('platforms', '0002_auto_20150718_0042'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platform',
            name='default_installer',
            field=jsonfield.fields.JSONField(null=True),
        ),
    ]
