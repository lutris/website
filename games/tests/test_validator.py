"""Tests for the installer validator"""
# pylint: disable=invalid-name, missing-docstring
import json
from django.test import TestCase
from runners.models import Runner
from games.models import Installer
from games.util.installer import validate_installer


class TestScriptValidator(TestCase):
    def setUp(self):
        self.installer = Installer(
            runner=Runner(name="Linux"),
            version="test",
        )

    def test_files_must_not_be_dict(self):
        self.installer.content = json.dumps({'files': {}})
        is_valid, errors = validate_installer(self.installer)
        self.assertFalse(is_valid, errors)

    def test_files_should_be_list(self):
        self.installer.content = json.dumps({'files': []})
        is_valid, errors = validate_installer(self.installer)
        self.assertTrue(is_valid, errors)

    def test_files_should_be_unique(self):
        self.installer.content = json.dumps({'files': [
            {'file1': 'http://foo'},
            {'file1': 'http://bar'},
        ]})
        is_valid, _errors = validate_installer(self.installer)
        self.assertFalse(is_valid, 'Files should be unique')

    def test_files_should_have_correct_attributes(self):
        """Files should have url and filename params"""
        self.installer.content = json.dumps({'files': [
            {'file1': {'foo': 'bar'}},
            {'file2': 'http://bar'}
        ]})
        is_valid, _errors = validate_installer(self.installer)
        self.assertFalse(is_valid)

        self.installer.content = json.dumps({'files': [
            {'file1': {'url': 'http://foo', 'filename': 'foo'}},
            {'file2': 'http://bar'}
        ]})
        is_valid, _errors = validate_installer(self.installer)
        self.assertTrue(is_valid)

    def test_task_have_names(self):
        self.installer.content = json.dumps({'installer': [
            {'task': {'name': 'create_prefix'}},
            {'task': {'name': 'winetricks', 'app': 'directx9'}}
        ]})
        is_valid, _errors = validate_installer(self.installer)
        self.assertTrue(is_valid)

        self.installer.content = json.dumps({'installer': [
            {'task': {'name': 'create_prefix'}},
            {'task': {'app': 'directx9'}}
        ]})
        is_valid, _errors = validate_installer(self.installer)
        self.assertFalse(is_valid)
        self.assertIn('name', _errors[0])

    def test_scummvm_script_requires_game_id(self):
        script = json.dumps({'game': {}})
        installer = Installer(
            runner=Runner(name="ScummVM", slug='scummvm'),
            content=script
        )
        is_valid, errors = validate_installer(installer)
        self.assertFalse(is_valid, errors)
        self.assertIn("ScummVM game should have a "
                      "game identifier in the 'game' section",
                      errors)

    def test_game_should_be_a_dict(self):
        self.installer.content = json.dumps({'game': ['foo', 'bar']})
        is_valid, _errors = validate_installer(self.installer)
        self.assertFalse(is_valid)

        self.installer.content = json.dumps(
            {'game': {'foo': 'bar', 'bar': 'foo'}}
        )
        is_valid, _errors = validate_installer(self.installer)
        self.assertTrue(is_valid)
