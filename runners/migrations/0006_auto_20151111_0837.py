# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runners', '0005_auto_20151106_0404'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='runtime',
            name='architecture',
        ),
        migrations.AddField(
            model_name='runtime',
            name='name',
            field=models.CharField(default='error', max_length=8),
            preserve_default=False,
        ),
    ]
