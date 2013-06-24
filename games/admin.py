"""Admin configuration for Lutris games"""
from django.contrib import admin

from . import models


class CompanyAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("name", )}
    ordering = ('name', )


class PlatformAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    ordering = ('name', )


class GameAdmin(admin.ModelAdmin):
    ordering = ("name", )
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('__unicode__', 'year', 'created', 'updated', 'is_public')
    list_filter = ('is_public', 'publisher', 'developer', 'genres')
    search_fields = ('name', )


class ScreenshotAdmin(admin.ModelAdmin):
    ordering = ("game__slug", "description")
    list_display = ("__unicode__", "uploaded_at", "published")
    list_editable = ("published", )


class FeaturedAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "created_at")
    #form = forms.FeaturedForm
    #raw_id_fields = ('game', )
    #autocomplete_lookup_fields = {
    #    'fk': ['game']
    #}

admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Screenshot, ScreenshotAdmin)
admin.site.register(models.Genre)
admin.site.register(models.Runner)
admin.site.register(models.Platform, PlatformAdmin)
admin.site.register(models.Company, CompanyAdmin)
admin.site.register(models.Installer)
admin.site.register(models.GameLibrary)
admin.site.register(models.Featured, FeaturedAdmin)
