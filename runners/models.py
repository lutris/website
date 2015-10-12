from django.db import models

from platforms.models import Platform

ARCH_CHOICES = (
    ('i386', '32 bit'),
    ('x86_64', '64 bit'),
    ('arm', 'ARM'),
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

    def save(self, *args, **kwargs):
        return super(Runner, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', )


class RunnerVersion(models.Model):
    class Meta(object):
        ordering = ('version', 'architecture')

    def __unicode__(self):
        return u"{} v{} ({})".format(self.runner.name,
                                     self.version,
                                     self.architecture)

    runner = models.ForeignKey(Runner, related_name='versions')
    version = models.CharField(max_length=32)
    architecture = models.CharField(max_length=8,
                                    choices=ARCH_CHOICES,
                                    default='x86_64')
    url = models.URLField(blank=True)
    default = models.BooleanField(default=False)


class Runtime(models.Model):
    architecture = models.CharField(max_length=8,
                                    choices=ARCH_CHOICES,
                                    default='x86_64')
    created_at = models.DateTimeField(auto_now=True)
    url = models.URLField()

    class Meta(object):
        ordering = ('-created_at', )

    def __unicode__(self):
        return u"{} runtime (uploaded on {})".format(self.architecture,
                                                     self.created_at)
