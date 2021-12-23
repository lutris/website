"""Admin settings for platorms app"""
from django.contrib import admin
from . import models
from . import forms


class PlatformAdmin(admin.ModelAdmin):
    """Admin configuration for platforms"""
    prepopulated_fields = {"slug": ("name",)}
    form = forms.PlatformForm
    ordering = ('name', )
    search_fields = ('name', )
    list_display = ('__str__', 'slug', 'has_auto_installer', 'igdb_id')


admin.site.register(models.Platform, PlatformAdmin)
