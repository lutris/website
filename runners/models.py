# pylint: disable=W0232,R0903
import re
from django.db import models

from platforms.models import Platform

ARCH_CHOICES = (
    ('i386', '32 bit'),
    ('x86_64', '64 bit'),
    ('armv7', 'ARM'),
    ('all', 'All'),
)


class Runner(models.Model):
    """ Model definition for the runners """
    name = models.CharField(max_length=127)
    slug = models.SlugField(unique=True)
    website = models.CharField(max_length=127, blank=True)
    icon = models.ImageField(upload_to='runners/icons', blank=True)
    platforms = models.ManyToManyField(Platform, related_name='runners')

    # pylint: disable=W0232, R0903
    class Meta(object):
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', )

    @property
    def versions(self):
        def version_key(runner_version):
            version = runner_version.version
            version_match = re.search(r'(\d[\d\.]+\d)', version)
            if not version_match:
                return
            version_number = version_match.groups()[0]
            prefix = version[0:version_match.span()[0]]
            suffix = version[version_match.span()[1]:]
            version = [int(p) for p in version_number.split('.')]
            version = version + [0] * (10 - len(version))
            version.append(prefix)
            version.append(suffix)
            return version
        return sorted(self.runner_versions.all(), key=version_key)


class RunnerVersion(models.Model):
    class Meta(object):
        ordering = ('version', 'architecture')

    def __unicode__(self):
        return u"{} v{} ({})".format(self.runner.name,
                                     self.version,
                                     self.architecture)

    runner = models.ForeignKey(Runner, related_name='runner_versions')
    version = models.CharField(max_length=32)
    architecture = models.CharField(max_length=8,
                                    choices=ARCH_CHOICES,
                                    default='x86_64')
    url = models.URLField(blank=True)
    default = models.BooleanField(default=False)


class Runtime(models.Model):
    name = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now=True)
    architecture = models.CharField(max_length=8,
                                    choices=ARCH_CHOICES,
                                    default='all')
    url = models.URLField()

    class Meta(object):
        ordering = ('-created_at', )

    def __unicode__(self):
        return u"{} runtime (uploaded on {})".format(self.name, self.created_at)
