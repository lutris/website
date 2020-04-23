"""Models for the common app"""
# pylint: disable=too-few-public-methods
import os
import shutil
import datetime
from django.db import models
from django.conf import settings
from django.urls import reverse
from markupfield.fields import MarkupField

from common.util import slugify


class News(models.Model):
    """News announcements, not currently used"""
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = MarkupField(markup_type='restructuredtext')
    publish_date = models.DateTimeField(default=datetime.datetime.now)
    image = models.ImageField(upload_to='news', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    class Meta:
        """Model configuration"""
        ordering = ['-publish_date']
        verbose_name_plural = "news"
        db_table = 'news'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Return the news' absolute URL"""
        return reverse('news_details', kwargs={'slug': self.slug}) + "#article"

    def save(self, force_insert=False, force_update=False, using=False,
             update_fields=False):
        self.slug = slugify(self.title)
        return super(News, self).save(force_insert=force_insert, force_update=force_insert,
                                      using=using, update_fields=update_fields)


class Upload(models.Model):
    """References to user uploaded files"""
    uploaded_file = models.FileField(upload_to='uploads')
    destination = models.CharField(max_length=256)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.uploaded_file.name

    def validate(self):
        """Validate an upload and move it to its destination"""
        destination = os.path.join(settings.FILES_ROOT, self.destination)
        if os.path.exists(destination):
            raise IOError("Can't overwrite files")
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))
        source = os.path.join(settings.MEDIA_ROOT, self.uploaded_file.name)
        shutil.move(source, destination)
        self.delete()
