"""Game views tests"""
# pylint: disable=no-member
import json
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from games.models import InstallerIssue
from . import factories


class TestInstallerViews(TestCase):
    """Test installer views"""
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
    """Test game list view"""

    def setUp(self):
        factories.CompanyFactory(name='Team 17', slug='team-17')

    def test_can_get_game_list(self):
        """Can get the basic game list"""
        url = reverse('game_list')
        self.assertEqual(url, "/games")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_can_receive_garbage_company(self):
        """The view should ignore bad company id values"""
        response = self.client.get("/games/by/1?companies=1'A=0")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/games/by/1?companies=1")
        self.assertEqual(response.status_code, 200)

    def test_can_receive_garbage_year(self):
        """The view should ignore bad year values"""
        url = (
            "/games/year/2009?page=2&paginate_by=25&ordering=name"
            "&years=2009%22%20or%20(1,2)=(select*from(select%20"
            "name_const(CHAR(111,108,111,108,111,115,104,101,114),1),"
            "name_const(CHAR(111,108,111,108,111,115,104,101,114),1))a)"
            "%20--%20%22x%22=%22x"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_can_receive_garbage_flag(self):
        """The view should ignore bad flags passed in the GET parameters"""
        url = "/games?q=launcher&flags==name"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_can_receive_garbage_ordering(self):
        """The view should ignore bad values for ordering"""
        url = "/games?ordering=name'A=0"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_can_receive_garbage_genre(self):
        """The view should ignore bad values for ordering"""
        url = "/games?ordering=name&genres=13'"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_can_receive_garbage_platform(self):
        """The view should ignore bad values for ordering"""
        url = "/games?ordering=name&platforms=16'A-"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_can_receive_garbage_page(self):
        """The view should ignore bad values for page"""
        url = "/games?page=xcvj234"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        url = "/games?page=-1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        url = "/games?page=0"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        url = "/games?page=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_can_receive_garbage_pagination_by(self):
        """The view should ignore bad values for pagination_values"""
        url = "/games?paginate_by=xcvj234"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        url = "/games?paginate_by=-1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        url = "/games?paginate_by=0"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class TestInstallerIssues(TestCase):
    def setUp(self):
        self.user = factories.UserFactory()
        self.game = factories.GameFactory()
        self.installer = factories.InstallerFactory(game=self.game)

    def test_get_issues(self):
        self.client.login(username=self.user.username, password="password")
        response = self.client.post(
            reverse('game-submit-issue'),
            {
                'installer': self.installer.slug,
                'content': 'Game does not launch'
            }
        )
        response = self.client.get(
            reverse('api_installer_issue', kwargs={'slug': self.game.slug})
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content['count'], 1)
        self.assertEqual(content['results'][0]['slug'], self.installer.slug)

    def test_cant_post_an_issue_if_not_logged_in(self):
        response = self.client.post(
            reverse('game-submit-issue'),
            {
                'installer': self.installer.slug,
                'content': 'Game does not launch'
            }
        )
        print(response)
        print(response.content)
        self.assertEqual(response.status_code, 302)

    def test_can_post_an_issue(self):
        """A logged in user should be able to create an issue"""
        self.client.login(username=self.user.username, password="password")
        response = self.client.post(
            reverse('game-submit-issue'),
            {
                'installer': self.installer.slug,
                'content': 'Game does not launch'
            }
        )
        content = response.json()
        self.assertEqual(content['status'], 'ok')
        self.assertEqual(response.status_code, 200)

    def test_can_post_a_reply(self):
        self.client.login(username=self.user.username, password="password")
        issue = InstallerIssue.objects.create(
            submitted_by=self.user,
            installer=self.installer,
            description="I can't launch the game hurr durr"
        )
        response = self.client.post(
            reverse('api_installer_issue_by_id', kwargs={'pk': issue.id}),
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
