# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import bitfield.models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0006_auto_20160509_2120'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='flags',
            field=bitfield.models.BitField(((b'fully_libre', b'Fully libre'), (b'open_engine', b'Open engine only'), (b'free', b'Free'), (b'freetoplay', b'Free-to-play'), (b'pwyw', b'Pay what you want'), (b'demo', b'Has a demo')), default=None),
        ),
    ]
