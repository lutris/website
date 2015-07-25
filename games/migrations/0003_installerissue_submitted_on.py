# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0002_auto_20150717_2226'),
    ]

    operations = [
        migrations.AddField(
            model_name='installerissue',
            name='submitted_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 7, 25, 4, 47, 44, 276882), auto_now_add=True),
            preserve_default=False,
        ),
    ]
