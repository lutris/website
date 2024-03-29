# Generated by Django 2.2.12 on 2021-12-23 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0047_auto_20211223_0618'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='game',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
