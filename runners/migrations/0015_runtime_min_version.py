# Generated by Django 4.2.1 on 2023-06-14 19:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runners', '0014_runtime_versioned'),
    ]

    operations = [
        migrations.AddField(
            model_name='runtime',
            name='min_version',
            field=models.CharField(blank=True, max_length=8),
        ),
    ]
