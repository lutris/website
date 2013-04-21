"""Admin configuration for Lutris games"""
from django.contrib import admin
from django.db import models as db_models

from games import models
from django_select2.widgets import Select2MultipleWidget, Select2Widget


class PlatformAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    ordering = ('name', )


class GameAdmin(admin.ModelAdmin):
    ordering = ("name", )
    list_display = ('__unicode__', 'year', 'created', 'updated', 'is_public')
    list_filter = ('is_public', 'publisher', 'developer', 'genres')
    formfield_overrides = {
        db_models.ManyToManyField: {'widget': Select2MultipleWidget},
        db_models.ForeignKey: {'widget': Select2Widget},
    }

    class Media:
        js = ('js/jquery-1.9.0.min.js', )


admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Screenshot)
admin.site.register(models.Genre)
admin.site.register(models.Runner)
admin.site.register(models.Platform, PlatformAdmin)
admin.site.register(models.Company)
admin.site.register(models.Installer)
