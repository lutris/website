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
        self.assertFalse(is_valid)

    def test_files_should_be_list(self):
        self.installer.content = json.dumps({'files': []})
        is_valid, errors = validate_installer(self.installer)
        self.assertTrue(is_valid)

    def test_scummvm_script_requires_game_id(self):
        script = json.dumps({'game': {}})
        installer = Installer(
            runner=Runner(name="scummvm"),
            content=script
        )
        is_valid, errors = validate_installer(installer)
        self.assertFalse(is_valid)
        self.assertIn("ScummVM game should have a "
                      "game identifier in the 'game' section",
                      errors)
