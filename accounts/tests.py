from django.test import TestCase
from django.test.client import Client

from django.contrib.auth.models import User

class TestRegistration(TestCase):

    def setUp(self):

        self.client = Client()

    def test_user_can_register(self):
        response = self.client.get("/user/register/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/user/register/", {
            'username': "testuser",
            'password1': "testpassword",
            'password2': "testpassword",
            'email': "test@lutris.net"
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        created_user = User.objects.get(username="testuser")
        self.assertFalse(created_user.is_active)
