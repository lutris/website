# Generated by Django 2.2.12 on 2022-01-06 23:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0050_auto_20211223_2347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gamealias',
            name='slug',
            field=models.SlugField(max_length=255),
        ),
    ]
