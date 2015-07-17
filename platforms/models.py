from django.db import models
from django.utils.translation import ugettext as _
from django.utils.text import slugify
from jsonfield import JSONField


class Platform(models.Model):
    """Gaming platform"""
    name = models.CharField(_('Name'), max_length=127)
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='platforms/icons', blank=True)
    default_installer = JSONField(null=True)

    # pylint: disable=W0232, R0903
    class Meta:
        ordering = ('name', )

    def __unicode__(self):
        return "%s" % self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(unicode(self.name))
        return super(Platform, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', )
