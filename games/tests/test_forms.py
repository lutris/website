from django.test import TestCase
from games import forms
from games.tests import factories


class TestInstallerForm(TestCase):
    def setUp(self):
        self.game = factories.GameFactory(name='Doom')
        self.runner = factories.RunnerFactory(name='Linux')
        self.installer = factories.InstallerFactory(game=self.game)

    def test_can_submit_installer(self):
        form_data = {
            'version': 'demo',
            'content': "exe: doom.x86",
            'runner': str(self.runner.id)
        }
        form = forms.InstallerForm(form_data, instance=self.installer)
        self.assertFalse(form.errors)
        self.assertTrue(form.is_valid())
        installer = form.save()
        self.assertEqual(installer.slug, 'doom-demo')

    def test_auto_increment_installer_slug(self):
        factories.InstallerFactory(version='zdoom', slug='doom-zdoom',
                                   game=self.game)
        form_data = {
            'version': 'zdoom',
            'content': "exe: doom.x86",
            'runner': str(self.runner.id)
        }
        form = forms.InstallerForm(form_data, instance=self.installer)
        self.assertTrue(form.is_valid())
        installer = form.save()
        self.assertEqual(installer.slug, 'doom-zdoom-1')

    def test_form_requires_runner(self):
        form_data = {
            'version': 'zdoom',
            'content': "exe: doom.x86",
        }
        form = forms.InstallerForm(form_data, instance=self.installer)
        self.assertFalse(form.is_valid())
