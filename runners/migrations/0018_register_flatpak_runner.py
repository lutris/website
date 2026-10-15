"""Register the Flatpak runner for website installer submissions."""

from django.db import migrations


def register_flatpak(apps, schema_editor):
    Runner = apps.get_model("runners", "Runner")
    Runner.objects.get_or_create(
        slug="flatpak",
        defaults={"name": "Flatpak", "website": "https://flatpak.org"},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("runners", "0017_runtime_version"),
    ]

    operations = [
        migrations.RunPython(register_flatpak, migrations.RunPython.noop),
    ]
