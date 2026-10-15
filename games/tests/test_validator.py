"""Tests for the installer validator"""

# pylint: disable=invalid-name, missing-docstring
import json

from django.test import TestCase

from games.models import Installer
from games.util.installer import validate_installer
from runners.models import Runner


class TestScriptValidator(TestCase):
    def setUp(self):
        self.installer = Installer(
            runner=Runner(name="Linux"),
            version="test",
        )

    def test_files_must_not_be_dict(self):
        self.installer.content = json.dumps({"files": {}})
        is_valid, errors = validate_installer(self.installer)
        self.assertFalse(is_valid, errors)

    def test_files_should_be_list(self):
        self.installer.content = json.dumps({"files": []})
        is_valid, errors = validate_installer(self.installer)
        self.assertTrue(is_valid, errors)

    def test_files_should_be_unique(self):
        self.installer.content = json.dumps(
            {
                "files": [
                    {"file1": "http://foo"},
                    {"file1": "http://bar"},
                ]
            }
        )
        is_valid, _errors = validate_installer(self.installer)
        self.assertFalse(is_valid, "Files should be unique")

    def test_files_should_have_correct_attributes(self):
        """Files should have url and filename params"""
        self.installer.content = json.dumps(
            {"files": [{"file1": {"foo": "bar"}}, {"file2": "http://bar"}]}
        )
        is_valid, _errors = validate_installer(self.installer)
        self.assertFalse(is_valid)

        self.installer.content = json.dumps(
            {
                "files": [
                    {"file1": {"url": "http://foo", "filename": "foo"}},
                    {"file2": "http://bar"},
                ],
                "installer": [
                    {"merge": {"src": "file1", "dst": "$GAMEDIR"}},
                    {"merge": {"src": "file2", "dst": "$GAMEDIR"}},
                ],
            }
        )
        is_valid, _errors = validate_installer(self.installer)
        self.assertTrue(is_valid)

    def test_task_have_names(self):
        self.installer.content = json.dumps(
            {
                "installer": [
                    {"task": {"name": "create_prefix"}},
                    {"task": {"name": "winetricks", "app": "directx9"}},
                ]
            }
        )
        is_valid, _errors = validate_installer(self.installer)
        self.assertTrue(is_valid)

        self.installer.content = json.dumps(
            {"installer": [{"task": {"name": "create_prefix"}}, {"task": {"app": "directx9"}}]}
        )
        is_valid, _errors = validate_installer(self.installer)
        self.assertFalse(is_valid)
        self.assertIn("name", _errors[0])

    def test_scummvm_script_requires_game_id(self):
        script = json.dumps({"game": {}})
        installer = Installer(runner=Runner(name="ScummVM", slug="scummvm"), content=script)
        is_valid, errors = validate_installer(installer)
        self.assertFalse(is_valid, errors)
        self.assertIn("ScummVM game should have a game identifier in the 'game' section", errors)

    def test_game_should_be_a_dict(self):
        self.installer.content = json.dumps({"game": ["foo", "bar"]})
        is_valid, _errors = validate_installer(self.installer)
        self.assertFalse(is_valid)

        self.installer.content = json.dumps({"game": {"foo": "bar", "bar": "foo"}})
        is_valid, _errors = validate_installer(self.installer)
        self.assertTrue(is_valid)

    def test_flatpak_requires_appid(self):
        self.installer.runner = Runner(name="Flatpak", slug="flatpak")
        self.installer.content = json.dumps({"game": {"args": "--fullscreen"}})
        valid, errors = validate_installer(self.installer)
        self.assertFalse(valid)
        self.assertIn("Flatpak installers require 'game.appid'.", errors)

    def test_flatpak_flathub_appid(self):
        self.installer.runner = Runner(name="Flatpak", slug="flatpak")
        self.installer.content = json.dumps({"game": {"appid": "org.example.Game"}})
        valid, errors = validate_installer(self.installer)
        self.assertTrue(valid, errors)

    def test_flatpak_bundle_task(self):
        self.installer.runner = Runner(name="Flatpak", slug="flatpak")
        self.installer.content = json.dumps({
            "game": {"appid": "org.example.Game"},
            "files": [{"bundle": "https://example.org/game.flatpak"}],
            "installer": [{"task": {"name": "install_flatpak", "file": "bundle"}}],
        })
        valid, errors = validate_installer(self.installer)
        self.assertTrue(valid, errors)

    def test_flatpak_bundle_task_unknown_file(self):
        self.installer.runner = Runner(name="Flatpak", slug="flatpak")
        self.installer.content = json.dumps({
            "game": {"appid": "org.example.Game"},
            "installer": [{"task": {"name": "install_flatpak", "file": "missing"}}],
        })
        valid, errors = validate_installer(self.installer)
        self.assertFalse(valid)
        self.assertTrue(any("unknown file" in error for error in errors))
