# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import markupfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True)),
                ('content', markupfield.fields.MarkupField(rendered_field=True)),
                ('content_markup_type', models.CharField(default=b'restructuredtext', max_length=30, editable=False, choices=[(b'', b'--'), (b'html', 'HTML'), (b'plain', 'Plain'), (b'restructuredtext', 'Restructured Text')])),
                ('publish_date', models.DateTimeField(default=datetime.datetime.now)),
                ('image', models.ImageField(null=True, upload_to=b'news', blank=True)),
                ('_content_rendered', models.TextField(editable=False)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-publish_date'],
                'db_table': 'news',
                'verbose_name_plural': 'news',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uploaded_file', models.FileField(upload_to=b'uploads')),
                ('destination', models.CharField(max_length=256)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('uploaded_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
