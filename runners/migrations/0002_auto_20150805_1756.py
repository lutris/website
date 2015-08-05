# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('runners', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='runnerversion',
            name='is_default',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='runner',
            name='name',
            field=models.CharField(max_length=127),
        ),
        migrations.AlterField(
            model_name='runner',
            name='website',
            field=models.CharField(max_length=127, blank=True),
        ),
    ]
