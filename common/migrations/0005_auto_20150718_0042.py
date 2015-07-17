# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0004_auto_20150717_2348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='content_markup_type',
            field=models.CharField(default=b'restructuredtext', max_length=30, editable=False, choices=[(b'', b'--'), (b'html', 'HTML'), (b'plain', 'Plain'), (b'restructuredtext', 'Restructured Text')]),
        ),
    ]
