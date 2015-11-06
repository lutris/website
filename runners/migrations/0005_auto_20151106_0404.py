# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runners', '0004_runtime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='runtime',
            name='created_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
