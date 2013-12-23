"""Admin configuration for Lutris games"""
from django.contrib import admin

from . import models


class CompanyAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("name", )}
    ordering = ('name', )


class PlatformAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    ordering = ('name', )


class InstallerAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'user', 'updated_at', 'published')
    list_filter = ('published', )
    list_editable = ('published', )
    ordering = ('-updated_at', )
    search_fields = ('slug', 'user__username')


class GenreAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    ordering = ('name', )


class RunnerAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("name", )}
    list_display = ('name', 'slug', 'website')


class GameAdmin(admin.ModelAdmin):
    ordering = ("name", )
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('__unicode__', 'year', 'created', 'updated', 'is_public')
    list_filter = ('is_public', 'publisher', 'developer', 'genres')
    search_fields = ('name', )
    raw_id_fields = ('publisher', 'developer', 'genres', 'platforms')
    autocomplete_lookup_fields = {
        'fk': ['publisher', 'developer'],
        'm2m': ['genres', 'platforms']
    }


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
admin.site.register(models.Genre, GenreAdmin)
admin.site.register(models.Runner, RunnerAdmin)
admin.site.register(models.Platform, PlatformAdmin)
admin.site.register(models.Company, CompanyAdmin)
admin.site.register(models.Installer, InstallerAdmin)
admin.site.register(models.GameLibrary)
admin.site.register(models.Featured, FeaturedAdmin)
