import os
import shutil
import datetime
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from markupfield.fields import MarkupField


class News(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = MarkupField(markup_type='restructuredtext')
    publish_date = models.DateTimeField(default=datetime.datetime.now)
    image = models.ImageField(upload_to='news', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    # pylint: disable=W0232, R0903
    class Meta(object):
        ordering = ['-publish_date']
        verbose_name_plural = "news"
        db_table = 'news'

    def __unicode__(self):
        return self.title

    # pylint: disable=E0202
    def get_absolute_url(self):
        return reverse('news_details', kwargs={'slug': self.slug}) + "#article"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        return super(News, self).save(*args, **kwargs)


class Upload(models.Model):
    uploaded_file = models.FileField(upload_to='uploads')
    destination = models.CharField(max_length=256)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL)

    def __unicode__(self):
        return self.uploaded_file.name

    def validate(self):
        destination = os.path.join(settings.FILES_ROOT, self.destination)
        if os.path.exists(destination):
            raise IOError("Can't overwrite files")
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))
        source = os.path.join(settings.MEDIA_ROOT, self.uploaded_file.name)
        shutil.move(source, destination)
        self.delete()
