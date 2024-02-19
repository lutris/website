# Generated by Django 4.2.1 on 2024-02-19 05:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0079_librarygame_updated_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="LibraryCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=256)),
                (
                    "gamelibrary",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="categories",
                        to="games.gamelibrary",
                    ),
                ),
            ],
        ),
    ]
