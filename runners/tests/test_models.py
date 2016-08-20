from django.test import TestCase
from runners.models import RunnerVersion, Runner


class TestRunnerVersions(TestCase):
    def setUp(self):
        self.runner = Runner.objects.create(name='wine')

    def test_versions_are_ordered_correctly(self):
        RunnerVersion.objects.create(runner=self.runner, version='1.9.14')
        RunnerVersion.objects.create(runner=self.runner, version='1.9.4')
        RunnerVersion.objects.create(runner=self.runner, version='1.9.1')
        RunnerVersion.objects.create(runner=self.runner, version='1.8')
        RunnerVersion.objects.create(runner=self.runner, version='1.7')
        RunnerVersion.objects.create(runner=self.runner, version='1.7.50')

        versions = self.runner.versions

        self.assertEqual(versions[0].version, '1.7')
        self.assertEqual(versions[1].version, '1.7.50')
        self.assertEqual(versions[2].version, '1.8')
        self.assertEqual(versions[3].version, '1.9.1')
        self.assertEqual(versions[4].version, '1.9.4')
        self.assertEqual(versions[5].version, '1.9.14')
