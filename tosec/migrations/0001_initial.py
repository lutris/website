# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('category', models.CharField(max_length=256)),
                ('version', models.CharField(max_length=32)),
                ('author', models.CharField(max_length=128)),
                ('section', models.CharField(default=b'TOSEC', max_length=12)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'Categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('category', models.ForeignKey(to='tosec.Category')),
            ],
            options={
                'ordering': ('category', 'name'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Rom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('size', models.IntegerField()),
                ('crc', models.CharField(max_length=16)),
                ('md5', models.CharField(max_length=32)),
                ('sha1', models.CharField(max_length=64)),
                ('game', models.ForeignKey(related_name='roms', to='tosec.Game')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
