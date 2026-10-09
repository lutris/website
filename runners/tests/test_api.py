import json
import os

from django.test import TestCase
from django.urls import reverse

from common.util import create_admin
from runners import models
from runners.views import ClientTooOld, get_client_version_number


class TestApi(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.runner = models.Runner(name="Wine", slug="wine")
        self.runner.save()
        self.runner_url = reverse("runner_detail", kwargs={"slug": "wine"})
        self.runner_upload_url = reverse("runner_upload", kwargs={"slug": "wine"})

        self.runner_version_data = {"version": "1.7.48", "architecture": "i386"}
        self.test_file_path = "/tmp/lutris-runner.dummy"
        with open(self.test_file_path, "w") as test_file:
            test_file.write("dummy file for lutris tests")

    def tearDown(self):
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_can_get_runner_details(self):
        response = self.client.get(self.runner_url)
        response = json.loads(response.content.decode())
        self.assertEqual(response["name"], "Wine")

    def test_anomymous_user_cant_upload_runners(self):
        response = self.client.put(
            self.runner_upload_url, json.dumps(self.runner_version_data), format="multipart"
        )
        self.assertEqual(response.status_code, 401)

    def test_can_upload_a_new_version(self):
        authenticated = self.client.login(username="admin", password="admin")
        self.assertTrue(authenticated)
        with open(self.test_file_path, "r") as fp:
            self.runner_version_data["file"] = fp
            response = self.client.post(
                self.runner_upload_url,
                self.runner_version_data,
                format="multipart",
            )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content.decode())
        self.assertIn("lutris-runner.dummy", response_data["versions"][0]["url"])


class TestRuntimeApi(TestCase):
    def setUp(self):
        models.Runtime.objects.create(name="dxvk", version="v1.10.3")
        self.latest_dxvk = models.Runtime.objects.create(name="dxvk", version="v2.7")

    def test_runtime_detail_with_duplicate_names_returns_latest(self):
        response = self.client.get(reverse("runtime_detail", kwargs={"name": "dxvk"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.latest_dxvk.id)

    def test_unknown_runtime_detail_returns_404(self):
        response = self.client.get(reverse("runtime_detail", kwargs={"name": "nope"}))
        self.assertEqual(response.status_code, 404)


class TestClientVersion(TestCase):
    def test_client_user_agent(self):
        self.assertEqual(get_client_version_number("Lutris 0.5.22"), 5022000)

    def test_slash_separated_user_agent(self):
        self.assertEqual(get_client_version_number("Lutris/0.5.22"), 5022000)

    def test_other_user_agents_have_no_version(self):
        self.assertEqual(get_client_version_number("curl/8.9.1"), 0)

    def test_lutris_user_agent_without_version_is_too_old(self):
        with self.assertRaises(ClientTooOld):
            get_client_version_number("Lutris")

    def test_runtime_versions_accepts_slash_separated_user_agent(self):
        response = self.client.get(reverse("runtime_versions"), HTTP_USER_AGENT="Lutris/0.5.22")
        self.assertEqual(response.status_code, 200)
