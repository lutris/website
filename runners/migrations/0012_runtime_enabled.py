# Generated by Django 2.2.12 on 2021-07-19 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runners', '0011_auto_20201012_0507'),
    ]

    operations = [
        migrations.AddField(
            model_name='runtime',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
    ]
