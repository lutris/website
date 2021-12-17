# pylint: disable=missing-docstring,too-few-public-methods,no-member
import re
from django.db import models

ARCH_CHOICES = (
    ("i386", "32 bit"),
    ("x86_64", "64 bit"),
    ("armv7", "ARM"),
    ("all", "All"),
)


class Runner(models.Model):
    """ Model definition for the runners """

    name = models.CharField(max_length=127)
    slug = models.SlugField(unique=True)
    website = models.CharField(max_length=127, blank=True)
    icon = models.ImageField(upload_to="runners/icons", blank=True)
    platforms = models.ManyToManyField("platforms.Platform", related_name="runners")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains",)

    @property
    def icon_url(self):
        if self.icon:
            return self.icon.url

    @property
    def versions(self):
        def version_key(runner_version):
            version = runner_version.version
            version_match = re.search(r"(\d[\d\.]+\d)", version)
            if not version_match:
                return []
            version_number = version_match.groups()[0]
            prefix = version[0: version_match.span()[0]]
            suffix = version[version_match.span()[1]:]
            version = [int(p) for p in version_number.split(".")]
            version = version + [0] * (10 - len(version))
            version.append(prefix)
            version.append(suffix)
            return version

        return sorted(self.runner_versions.all(), key=version_key)


class RunnerVersion(models.Model):
    runner = models.ForeignKey(
        Runner, related_name="runner_versions", on_delete=models.CASCADE
    )
    version = models.CharField(max_length=32)
    architecture = models.CharField(
        max_length=8, choices=ARCH_CHOICES, default="x86_64"
    )
    url = models.URLField(blank=True)
    default = models.BooleanField(default=False)

    class Meta:
        ordering = ("version", "architecture")

    def __str__(self):
        return u"{} {} ({})".format(self.runner.name, self.version, self.architecture)

    @property
    def full_version(self):
        return "%s-%s" % (self.version, self.architecture)


class Runtime(models.Model):
    """Model class for runtime components"""

    name = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now=True)
    architecture = models.CharField(max_length=8, choices=ARCH_CHOICES, default="all")
    url = models.URLField(blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return u"{} runtime (uploaded on {})".format(self.name, self.created_at)


class RuntimeComponent(models.Model):
    """Individual file from a runtime"""
    runtime = models.ForeignKey(Runtime, related_name="components", on_delete=models.CASCADE)
    filename = models.CharField(max_length=512)
    url = models.URLField()
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("filename", )

    def __str__(self):
        return self.filename
