# Generated by Django 2.2.12 on 2022-05-31 23:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('providers', '0010_providergame_internal_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='providergenre',
            name='internal_id',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='providerplatform',
            name='internal_id',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
