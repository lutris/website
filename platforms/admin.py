from django.contrib import admin
from . import models


class PlatformAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    ordering = ('name', )
    search_fields = ('name', )


admin.site.register(models.Platform, PlatformAdmin)
