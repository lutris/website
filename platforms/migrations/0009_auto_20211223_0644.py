# Generated by Django 2.2.12 on 2021-12-23 06:44

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('platforms', '0008_platform_short_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='platform',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='platform',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
