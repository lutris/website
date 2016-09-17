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


class TestGameForm(TestCase):
    def setUp(self):
        self.platform = factories.PlatformFactory()
        self.genre = factories.GenreFactory()
        self.existing_game = factories.GameFactory(
            name="Hyperdimension Neptunia Re;Birth2: Sisters Generation"
        )

    def test_can_validate_basic_data(self):
        form = forms.GameForm({
            'name': 'bliblu',
            'platforms': [self.platform.id],
            'genres': [self.genre.id],

        })
        self.assertTrue(form.is_valid())

    def test_catches_duplicate_slugs(self):
        form = forms.GameForm({
            'name': 'Hyperdimension Neptunia Re,Birth2: Sisters Generation',
            'platforms': [self.platform.id],
            'genres': [self.genre.id],

        })
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
