# Generated by Django 4.2.1 on 2023-05-16 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bundles', '0002_bundle_games'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bundle',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]