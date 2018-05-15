# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('platforms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Runner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=127, verbose_name='Name')),
                ('slug', models.SlugField(unique=True)),
                ('website', models.CharField(max_length=127, verbose_name='Website', blank=True)),
                ('icon', models.ImageField(upload_to=b'runners/icons', blank=True)),
                ('platforms', models.ManyToManyField(related_name='runners', to='platforms.Platform')),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RunnerVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.CharField(max_length=32)),
                ('architecture', models.CharField(default=b'x86_64', max_length=8, choices=[(b'i386', b'32 bit'), (b'x86_64', b'64 bit'), (b'arm', b'ARM')])),
                ('url', models.URLField(blank=True)),
                ('runner', models.ForeignKey(related_name='versions', to='runners.Runner', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('version', 'architecture'),
            },
            bases=(models.Model,),
        ),
    ]
