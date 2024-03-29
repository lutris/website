# Generated by Django 4.2.1 on 2023-07-19 06:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('hardware', '0001_initial'), ('hardware', '0002_alter_device_name_alter_subsystem_name_and_more'), ('hardware', '0003_alter_device_comment_alter_device_name'), ('hardware', '0004_alter_subsystem_name'), ('hardware', '0005_alter_subsystem_subdevice_id'), ('hardware', '0006_feature_alter_vendor_options_generation'), ('hardware', '0007_feature_featureset_alter_feature_version')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vendor_id', models.CharField(max_length=4, unique=True)),
                ('name', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_id', models.CharField(max_length=4)),
                ('name', models.CharField(blank=True, max_length=256)),
                ('comment', models.CharField(blank=True, max_length=256)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hardware.vendor')),
            ],
        ),
        migrations.CreateModel(
            name='Subsystem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subvendor_id', models.CharField(max_length=4)),
                ('subdevice_id', models.CharField(max_length=32)),
                ('name', models.CharField(blank=True, max_length=256)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hardware.device')),
            ],
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('version', models.CharField(blank=True, max_length=8)),
                ('featureset', models.CharField(blank=True, max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='Generation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('year', models.SmallIntegerField()),
                ('features', models.ManyToManyField(to='hardware.feature')),
                ('vendor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='hardware.vendor')),
            ],
        ),
    ]
