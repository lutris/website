# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('runners', '0002_auto_20150805_1756'),
    ]

    operations = [
        migrations.RenameField(
            model_name='runnerversion',
            old_name='is_default',
            new_name='default',
        ),
    ]
