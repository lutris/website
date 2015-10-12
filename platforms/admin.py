from django.contrib import admin
from . import models
from . import forms


class PlatformAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    form = forms.PlatformForm
    ordering = ('name', )
    search_fields = ('name', )


admin.site.register(models.Platform, PlatformAdmin)
