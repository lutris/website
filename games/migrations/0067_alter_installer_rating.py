# Generated by Django 4.2.1 on 2023-06-12 19:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0066_alter_autoinstaller_id_alter_company_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='installer',
            name='rating',
            field=models.CharField(blank=True, choices=[('0', 'Do not use')], max_length=24),
        ),
    ]
