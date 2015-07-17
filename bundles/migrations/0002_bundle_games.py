# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
        ('bundles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bundle',
            name='games',
            field=models.ManyToManyField(related_name='bundles', to='games.Game'),
            preserve_default=True,
        ),
    ]
