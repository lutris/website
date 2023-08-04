"""Models for the common app"""
# pylint: disable=too-few-public-methods,no-member
import os
import shutil
import datetime
from django.db import models
from django.conf import settings
from common.spaces import SpacesBucket


class News(models.Model):
    """News announcements, not currently used"""
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField(blank=True)
    publish_date = models.DateTimeField(default=datetime.datetime.now)
    image = models.ImageField(upload_to='news', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        """Model configuration"""
        verbose_name_plural = "news"
        db_table = 'news'

class Upload(models.Model):
    """References to user uploaded files"""
    uploaded_file = models.FileField(upload_to='uploads')
    destination = models.CharField("destination path", max_length=256)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    hosting = models.CharField(
        max_length=8,
        choices=[("local", "Local"), ("spaces", "Spaces")],
        default="local"
    )

    def __str__(self):
        return self.uploaded_file.name

    @property
    def source_path(self):
        """Absolute path for the uploaded file"""
        if self.uploaded_file:
            return os.path.join(settings.MEDIA_ROOT, self.uploaded_file.name)
        return None

    def move_to_local_hosting(self):
        """Move the file to its destination"""
        destination = os.path.join(settings.FILES_ROOT, self.destination)
        if os.path.exists(destination):
            raise IOError("Can't overwrite files")
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))
        shutil.move(self.source_path, destination)

    def upload_to_spaces(self):
        """Upload the file to Digital Ocean Spaces"""
        space = SpacesBucket()
        space.upload(self.source_path, self.destination, public=True)

    def validate(self):
        """Validate an upload and move it to its destination"""
        if self.hosting == "spaces":
            self.upload_to_spaces()
        else:
            self.move_to_local_hosting()
        self.delete()


class KeyValueStore(models.Model):
    """Generic key value store"""
    key = models.CharField(max_length=64)
    value = models.CharField(max_length=1024, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.key)


def save_action_log(key, value):
    """Save the results of a task as a KeyValueStore object"""
    log_object = KeyValueStore.objects.create(key=key)
    log_object.value = str(value)
    log_object.save()
