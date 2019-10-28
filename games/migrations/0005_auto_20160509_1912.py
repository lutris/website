# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0004_auto_20150805_1756'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='gogid',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='game',
            name='humblestoreid',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='game',
            name='epicgamesid',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='is_public',
            field=models.BooleanField(default=False, verbose_name=b'Published'),
        ),
    ]
