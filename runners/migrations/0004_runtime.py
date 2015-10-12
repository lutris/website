# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('runners', '0003_auto_20150805_1757'),
    ]

    operations = [
        migrations.CreateModel(
            name='Runtime',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('architecture', models.CharField(default=b'x86_64', max_length=8, choices=[(b'i386', b'32 bit'), (b'x86_64', b'64 bit'), (b'arm', b'ARM')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('url', models.URLField()),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
    ]
