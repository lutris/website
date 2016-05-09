# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0005_auto_20160509_1912'),
    ]

    operations = [
        migrations.AlterField(
            model_name='installer',
            name='notes',
            field=models.TextField(),
        ),
    ]
