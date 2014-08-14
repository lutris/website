"""Admin configuration for Lutris games"""
from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple
from django.contrib import admin

from . import models
from . import forms


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


class RunnerVersionInline(admin.TabularInline):
    model = models.RunnerVersion


class RunnerAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("name", )}
    list_display = ('name', 'slug', 'website')
    inlines = [
        RunnerVersionInline,
    ]


class GameMetadataInline(admin.TabularInline):
    model = models.GameMetadata


class GameAdmin(admin.ModelAdmin):
    ordering = ("-created", )
    form = forms.BaseGameForm
    list_display = ('__unicode__', 'year', 'steamid',
                    'created', 'updated', 'is_public')
    list_filter = ('is_public', 'publisher', 'developer', 'genres')
    list_editable = ('is_public', )
    search_fields = ('name', 'steamid')
    raw_id_fields = ('publisher', 'developer', 'genres', 'platforms')
    autocomplete_lookup_fields = {
        'fk': ['publisher', 'developer'],
        'm2m': ['genres', 'platforms']
    }
    formfield_overrides = {
        BitField: {'widget': BitFieldCheckboxSelectMultiple}
    }
    inlines = [
        GameMetadataInline,
    ]


class ScreenshotAdmin(admin.ModelAdmin):
    ordering = ("game__slug", "description")
    list_display = ("__unicode__", "uploaded_at", "published")
    list_editable = ("published", )


class FeaturedAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "created_at")

admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Screenshot, ScreenshotAdmin)
admin.site.register(models.Genre, GenreAdmin)
admin.site.register(models.Runner, RunnerAdmin)
admin.site.register(models.Platform, PlatformAdmin)
admin.site.register(models.Company, CompanyAdmin)
admin.site.register(models.Installer, InstallerAdmin)
admin.site.register(models.GameLibrary)
admin.site.register(models.Featured, FeaturedAdmin)
