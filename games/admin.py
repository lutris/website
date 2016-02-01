"""Admin configuration for Lutris games"""
# pylint: disable=R0201
from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple
from django.core.urlresolvers import reverse
from django.contrib import admin

from . import models
from . import forms


class CompanyAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("name", )}
    ordering = ('name', )
    search_fields = ('name', )


class InstallerAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'runner', 'game_link', 'user',
                    'created_at', 'updated_at', 'published')
    list_filter = ('published', 'runner')
    list_editable = ('published', )
    ordering = ('-created_at', )
    readonly_fields = ('game_link',)
    search_fields = ('slug', 'user__username', 'content')

    def game_link(self, obj):
        return u"<a href='{0}'>{1}<a/>".format(
            reverse("admin:games_game_change", args=(obj.game.id, )),
            obj.game
        )
    game_link.allow_tags = True
    game_link.short_description = "Game (link)"


class InstallerIssueAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'submitted_by', 'submitted_on', 'installer')


class GenreAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    ordering = ('name', )


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
    ordering = ("-uploaded_at", )
    list_display = ("__unicode__", "game_link", "uploaded_at", "published")
    list_editable = ("published", )
    readonly_fields = ('game_link',)
    search_fields = ['game__name']

    def game_link(self, obj):
        return u"<a href='{0}'>{1}<a/>".format(
            reverse("admin:games_game_change", args=(obj.game.id, )),
            obj.game
        )
    game_link.allow_tags = True
    game_link.short_description = "Game (link)"


class FeaturedAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "created_at")


class GameSubmissionAdmin(admin.ModelAdmin):
    list_display = ("game_link", "user_link", "created_at", "accepted_at")

    def game_link(self, obj):
        return u"<a href='{0}'>{1}<a/>".format(
            reverse("admin:games_game_change", args=(obj.game.id, )),
            obj.game
        )
    game_link.allow_tags = True
    game_link.short_description = "Game"

    def user_link(self, obj):
        return u"<a href='{0}'>{1}</a>".format(
            reverse("admin:accounts_user_change", args=(obj.user.id, )),
            obj.user
        )
    user_link.allow_tags = True
    user_link.short_description = "User"


admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Screenshot, ScreenshotAdmin)
admin.site.register(models.Genre, GenreAdmin)
admin.site.register(models.Company, CompanyAdmin)
admin.site.register(models.Installer, InstallerAdmin)
admin.site.register(models.InstallerIssue, InstallerIssueAdmin)
admin.site.register(models.GameLibrary)
admin.site.register(models.Featured, FeaturedAdmin)
admin.site.register(models.GameSubmission, GameSubmissionAdmin)
