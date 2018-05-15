# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import bitfield.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('runners', '0001_initial'),
        ('contenttypes', '0001_initial'),
        ('platforms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=127, verbose_name='Name')),
                ('slug', models.SlugField(unique=True)),
                ('logo', models.ImageField(upload_to=b'companies/logos', blank=True)),
                ('website', models.CharField(max_length=128, blank=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'companies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Featured',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('image', models.ImageField(upload_to=b'featured')),
                ('description', models.CharField(max_length=255, null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.SET_NULL)),
            ],
            options={
                'verbose_name': 'Featured content',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('year', models.IntegerField(null=True, blank=True)),
                ('website', models.CharField(max_length=200, blank=True)),
                ('icon', models.ImageField(upload_to=b'games/icons', blank=True)),
                ('title_logo', models.ImageField(upload_to=b'games/banners', blank=True)),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False, verbose_name=b'Published on website')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('steamid', models.PositiveIntegerField(null=True, blank=True)),
                ('flags', bitfield.models.BitField(((b'fully_libre', b'Fully libre'), (b'open_engine', b'Open engine only'), (b'free', b'Free'), (b'freetoplay', b'Free-to-play'), (b'pwyw', b'Pay what you want')), default=None)),
                ('developer', models.ForeignKey(related_name='developed_game', blank=True, to='games.Company', null=True, on_delete=models.SET_NULL)),
            ],
            options={
                'ordering': ['name'],
                'permissions': (('can_publish_game', 'Can make the game visible'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GameLibrary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('games', models.ManyToManyField(to='games.Game')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'game libraries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GameMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=16)),
                ('value', models.CharField(max_length=255)),
                ('game', models.ForeignKey(to='games.Game', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GameSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('accepted_at', models.DateTimeField(null=True)),
                ('game', models.ForeignKey(to='games.Game', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'User submitted game',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Installer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True)),
                ('version', models.CharField(max_length=32)),
                ('description', models.CharField(max_length=512, null=True, blank=True)),
                ('notes', models.CharField(max_length=512, blank=True)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published', models.BooleanField(default=False)),
                ('game', models.ForeignKey(to='games.Game', on_delete=models.CASCADE)),
                ('runner', models.ForeignKey(to='runners.Runner', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InstallerIssue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField()),
                ('installer', models.ForeignKey(to='games.Installer', on_delete=models.CASCADE)),
                ('submitted_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Screenshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(upload_to=b'games/screenshots')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('description', models.CharField(max_length=256, null=True, blank=True)),
                ('published', models.BooleanField(default=False)),
                ('game', models.ForeignKey(to='games.Game', on_delete=models.CASCADE)),
                ('uploaded_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='game',
            name='genres',
            field=models.ManyToManyField(to='games.Genre', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='game',
            name='platforms',
            field=models.ManyToManyField(to='platforms.Platform', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='game',
            name='publisher',
            field=models.ForeignKey(related_name='published_game', blank=True, to='games.Company', null=True, on_delete=models.SET_NULL),
            preserve_default=True,
        ),
    ]
