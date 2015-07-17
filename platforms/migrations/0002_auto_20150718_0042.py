# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('platforms', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='platform',
            name='default_installer',
            field=jsonfield.fields.JSONField(default='', blank=True),
            preserve_default=False,
        ),
    ]
