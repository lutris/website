# pylint: disable=R0903
from django.db import models
from django.db.models import Count
from django.utils.text import slugify
from jsonfield import JSONField


class PlatformManager(models.Manager):
    def with_games(self):
        from games.models import Game
        platform_list = (
            Game.objects.with_installer()
            .values_list('platforms')
            .annotate(p_count=Count('platforms'))
            .filter(p_count__gt=0)
        )
        platform_ids = [platform[0] for platform in platform_list]
        return self.get_queryset().filter(id__in=platform_ids)


class Platform(models.Model):
    """Gaming platform"""
    name = models.CharField(max_length=127)
    slug = models.SlugField(unique=True)
    icon = models.ImageField(upload_to='platforms/icons', blank=True)
    default_installer = JSONField(null=True)
    tgdb_name = models.CharField(max_length=255, blank=True)

    objects = PlatformManager()

    # pylint: disable=W0232, R0903
    class Meta:
        ordering = ('name', )

    def __unicode__(self):
        return "%s" % self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Platform, self).save(*args, **kwargs)

    @staticmethod
    def autocomplete_search_fields():
        return ('name__icontains', )

    def has_auto_installer(self):
        return bool(self.default_installer)
    has_auto_installer.boolean = True  # Display icon in admin
