from django.test import TestCase
from games.util.installer import ScriptValidator


class TestScriptValidator(TestCase):
    def test_files_must_not_be_dict(self):
        installer = {'files': {}}
        validator = ScriptValidator(installer)
        self.assertFalse(validator.is_valid())

    def test_files_should_be_list(self):
        installer = {'files': []}
        validator = ScriptValidator(installer)
        self.assertTrue(validator.is_valid())

    def test_scummvm_script_requires_game_id(self):
        installer = {
            'runner': "scummvm",
            'game': {}
        }
        validator = ScriptValidator(installer)
        self.assertFalse(validator.is_valid())
        self.assertIn("ScummVM game should have a "
                      "game identifier in the 'game' section",
                      validator.errors)
