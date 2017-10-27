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


class TestGameEditForm(TestCase):
    """Test suite for the form to suggest game changes"""

    def setUp(self):
        name = 'Horribly Misspelled Game Title'
        platform = factories.PlatformFactory()
        genre = factories.GenreFactory()
        year = 2012
        website = 'https://example.com'

        self.game = factories.GameFactory(name=name)
        self.game.platforms.set([platform.id])
        self.game.genres.set([genre.id])
        self.game.website = website
        self.game.year = year
        self.game.description = ''
        self.game.save()

        self.inputs = {
            'name': name,
            'platforms': [platform.id],
            'genres': [genre.id],
            'website': website,
            'year': year,
            'description': ''
        }

    def test_user_cannot_submit_unchanged_form(self):
        """Ensures that a user cannot submit an unchanged form"""

        # Create form
        form = forms.GameEditForm(self.inputs, initial=self.game.get_change_model())

        # Form should not be valid since no changes were made
        self.assertFalse(form.is_valid())
        self.assertIn('You have not changed anything', str(form.errors))

    def test_user_can_submit_valid_changed_form(self):
        """Ensures that a user can submit valid changes"""

        # Prepare the change to be suggested
        self.inputs['name'] = 'Corrected Game Title'

        # Needed for the foreign key of the change row
        change_for = self.game.get_change_model()

        # Create form
        form = forms.GameEditForm(self.inputs, initial=change_for)

        # Assert that form is valid since the change is valid
        self.assertTrue(form.is_valid())

        # Persist changes
        change_suggestion = form.save(commit=False)
        change_suggestion.change_for = self.game
        change_suggestion.save()
        form.save_m2m()

        # Assert that the changes are in the model
        self.assertEqual(change_suggestion.name, 'Corrected Game Title')

        # Finally, verify the diff (did only the name change?)
        diff = change_suggestion.get_changes()

        # Count should be 1 since only one change was made
        self.assertEqual(len(diff), 1)

        # Untie
        (diff_name, diff_old, diff_new) = diff[0]

        # Verify diff
        self.assertEqual(diff_name, 'name')
        self.assertEqual(diff_old, 'Horribly Misspelled Game Title')
        self.assertEqual(diff_new, 'Corrected Game Title')

    def test_user_cannot_submit_invalid_changed_form(self):
        """Ensures that a user cannot submit invalid changes"""

        # Prepare the change to be suggested (which is invalid here)
        self.inputs['name'] = ''

        # Create form
        form = forms.GameEditForm(self.inputs, initial=self.game.get_change_model())

        # Assert that form is invalid since the name must not be empty
        self.assertFalse(form.is_valid())
        self.assertIn('This field is required', str(form.errors['name']))
