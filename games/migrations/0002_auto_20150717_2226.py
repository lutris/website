# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='genres',
            field=models.ManyToManyField(to='games.Genre'),
        ),
        migrations.AlterField(
            model_name='game',
            name='platforms',
            field=models.ManyToManyField(to='platforms.Platform'),
        ),
    ]
