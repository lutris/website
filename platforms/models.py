"""Platform models"""
# pylint: disable=R0903
from django.db import models
from jsonfield import JSONField
from common.util import slugify

class Platform(models.Model):
    """Gaming platform"""
    name = models.CharField(max_length=127)
    short_name = models.CharField(max_length=32, null=True, blank=True)
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='platforms/icons', blank=True)
    default_installer = JSONField(null=True)
    tgdb_name = models.CharField(max_length=255, blank=True)
    igdb_id = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # pylint: disable=W0232, R0903
    class Meta:
        ordering = ('name', )

    def __str__(self):
        return "%s" % (self.short_name or self.name)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.slug:
            self.slug = slugify(str(self.name))
        return super(Platform, self).save(force_insert=force_insert, force_update=force_update,
                                          using=using, update_fields=update_fields)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', )

    def has_auto_installer(self):
        return bool(self.default_installer)
    has_auto_installer.boolean = True  # Display icon in admin
