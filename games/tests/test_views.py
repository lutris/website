# pylint: disable=missing-docstring
import json
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from games.models import InstallerIssue
from . import factories


class TestInstallerViews(TestCase):
    def setUp(self):
        self.game = factories.GameFactory(name='doom', slug='doom')
        self.user = factories.UserFactory()

    def test_anonymous_user_cant_create_installer(self):
        factories.GameFactory()
        installer_url = reverse("new_installer", kwargs={'slug': 'doom'})
        response = self.client.get(installer_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(settings.LOGIN_URL + '?next=' + installer_url,
                         response.redirect_chain[1][0])

    def test_logged_in_user_can_create_installer(self):
        self.client.login(username=self.user.username, password="password")
        installer_url = reverse("new_installer", kwargs={'slug': 'doom'})
        response = self.client.get(installer_url)
        self.assertEqual(response.status_code, 200)

    def test_can_redirect_to_game_page_from_installer_slug(self):
        installer = factories.InstallerFactory(game=self.game)

        game_for_installer_url = reverse("game_for_installer",
                                         kwargs={'slug': installer.slug})
        response = self.client.get(game_for_installer_url)
        self.assertRedirects(
            response, reverse('game_detail', kwargs={'slug': self.game.slug})
        )

    def test_can_access_installer_feed(self):
        response = self.client.get('/games/installer/feed/')
        self.assertEqual(response.status_code, 200)


class TestGameViews(TestCase):
    def test_can_get_game_list(self):
        response = self.client.get(reverse('game_list'))
        self.assertEqual(response.status_code, 200)


class TestInstallerIssues(TestCase):
    def setUp(self):
        self.user = factories.UserFactory()
        self.game = factories.GameFactory()
        self.installer = factories.InstallerFactory(game=self.game)

    def test_get_issues(self):
        response = self.client.get(
            reverse('api_installer_issue', kwargs={'slug': self.game.slug})
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content['count'], 1)
        self.assertEqual(content['results'][0]['slug'], self.installer.slug)

    def test_cant_post_an_issue_if_not_logged_in(self):
        response = self.client.post(
            reverse('api_installer_issue_create', kwargs={
                'game_slug': self.game.slug,
                'installer_slug': self.installer.slug
            }),
            {
                'slug': self.installer.slug,
                'description': 'Game does not launch'
            }
        )
        self.assertEqual(response.status_code, 401)

    def test_can_post_an_issue(self):
        self.client.login(username=self.user.username, password="password")
        response = self.client.post(
            reverse('api_installer_issue_create', kwargs={
                'game_slug': self.game.slug,
                'installer_slug': self.installer.slug
            }),
            json.dumps({
                'slug': self.installer.slug,
                'description': 'Game does not launch'
            }),
            content_type='application/json'
        )
        content = response.json()
        self.assertEqual(content['submitted_by'], self.user.id)
        self.assertEqual(content['description'], 'Game does not launch')
        self.assertEqual(response.status_code, 201)

    def test_can_post_a_reply(self):
        self.client.login(username=self.user.username, password="password")
        issue = InstallerIssue.objects.create(
            submitted_by=self.user,
            installer=self.installer,
            description="I can't launch the game hurr durr"
        )
        response = self.client.post(
            reverse('api_installer_issue_by_id', kwargs={
                'pk': issue.id
            }),
            json.dumps({
                'description': 'try blowing in the cartridge'
            }),
            content_type='application/json'
        )
        content = response.json()
        self.assertEqual(content['submitted_by'], self.user.id)
        self.assertIn('cartridge', content['description'])
        self.assertEqual(response.status_code, 201)

    def test_can_mark_an_issue_as_solved(self):
        self.client.login(username=self.user.username, password="password")
        issue = InstallerIssue.objects.create(
            submitted_by=self.user,
            installer=self.installer,
            description="I can't launch the game hurr durr"
        )
        response = self.client.patch(
            reverse('api_installer_issue_by_id', kwargs={
                'pk': issue.id
            }),
            json.dumps({
                'solved': True
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content['solved'], True)
