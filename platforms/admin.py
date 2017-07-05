from django.contrib import admin
from . import models
from . import forms


class PlatformAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    form = forms.PlatformForm
    ordering = ('name', )
    search_fields = ('name', )
    list_display = ('__unicode__', 'slug', 'has_auto_installer')


admin.site.register(models.Platform, PlatformAdmin)
