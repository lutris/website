import os
import json
from django.test import TestCase
from django.core.urlresolvers import reverse
from runners import models
from common.util import create_admin


class TestApi(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.runner = models.Runner(
            name="Wine",
            slug="wine"
        )
        self.runner.save()
        self.runner_url = reverse("runner_detail", kwargs={"slug": "wine"})
        self.runner_upload_url = reverse("runner_upload",
                                         kwargs={"slug": "wine"})

        self.runner_version_data = {
            "version": "1.7.48",
            "architecture": "i386"
        }
        self.test_file_path = '/tmp/lutris-runner.dummy'
        with open(self.test_file_path, 'w') as test_file:
            test_file.write('dummy file for lutris tests')

    def tearDown(self):
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_can_get_runner_details(self):
        response = self.client.get(self.runner_url)
        response = json.loads(response.content)
        self.assertEqual(response["name"], "Wine")

    def test_anomymous_user_cant_upload_runners(self):
        response = self.client.put(
            self.runner_upload_url,
            json.dumps(self.runner_version_data),
            format='multipart'
        )
        self.assertEqual(response.status_code, 401)

    def test_can_upload_a_new_version(self):
        authenticated = self.client.login(username='admin', password='admin')
        self.assertTrue(authenticated)
        with open(self.test_file_path, 'r') as fp:
            self.runner_version_data['file'] = fp
            response = self.client.post(
                self.runner_upload_url,
                self.runner_version_data,
                format='multipart',
            )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertIn('lutris-runner.dummy',
                      response_data['versions'][0]['url'])
