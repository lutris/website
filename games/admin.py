"""Admin configuration for Lutris games"""
# pylint: disable=too-few-public-methods,missing-docstring,no-self-use
from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from reversion.admin import VersionAdmin

from . import forms, models


class GameFilter(admin.SimpleListFilter):
    """Simple filter to remove clutter from the admin panel"""

    title = 'Show'
    parameter_name = 'change_for'

    def lookups(self, request, model_admin):
        # Available fitlers
        return (
            (None, 'Only games (default)'),
            ('only-games-with-changes', 'Only games with suggested changes'),
            ('only-changes', 'Only suggested changes'),
            ('all', 'All'),
        )

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': changelist.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        # Filter queryset according to the selected filter
        if self.value() is None:
            return queryset.filter(change_for__isnull=True)
        elif self.value() == 'only-games-with-changes':
            subqueryset = (
                queryset.values('change_for__id')
                .filter(change_for__isnull=False)
                .distinct()
            )
            return queryset.filter(change_for__isnull=True, id__in=subqueryset)
        elif self.value() == 'only-changes':
            return queryset.filter(change_for__isnull=False)


class CompanyAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("name", )}
    ordering = ('name', )
    search_fields = ('name', )
    list_display = ('__str__', 'id', 'website')


class InstallerAdmin(VersionAdmin):
    list_display = ('__str__', 'runner', 'version', 'game_link', 'user',
                    'created_at', 'updated_at', 'published', 'draft')
    list_filter = ('published', 'runner', 'version')
    list_editable = ('published', )
    ordering = ('-created_at', )
    readonly_fields = ('game_link', 'created_at', 'updated_at', 'published_by')
    search_fields = ('slug', 'user__username', 'content')

    raw_id_fields = ('game', 'user')
    autocomplete_lookup_fields = {
        'fk': ['game', 'user'],
    }

    def game_link(self, obj):
        return mark_safe("<a href='{0}'>{1}<a/>".format(
            reverse("admin:games_game_change", args=(obj.game.id, )),
            obj.game
        ))
    game_link.short_description = "Game (link)"


class IssueReplyInline(admin.StackedInline):
    """Admin config for issue replies"""
    model = models.InstallerIssueReply
    extra = 1
    readonly_fields = (
        'submitted_by',
        'submitted_on',
        'issue'
    )

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        class DefaultUserFormSet(formset):
            """Sets every instance of the formset to a given user"""

            def save_new_objects(self, commit=True):  # pylint: disable=unused-argument
                """Force commit to false to prevent IntegrityErrors then set
                the user. You must set this attribute yourself.
                """
                self.saved_forms = []  # pylint: disable=attribute-defined-outside-init
                objects = super().save_new_objects(commit=False)
                for obj in objects:
                    obj.submitted_by = self.user
                    obj.save()
                return objects

        DefaultUserFormSet.user = request.user
        return DefaultUserFormSet


class InstallerIssueAdmin(admin.ModelAdmin):
    """Admin config for issues"""
    list_display = ('__str__', 'submitted_by', 'submitted_on', 'installer')
    readonly_fields = (
        'submitted_by',
        'submitted_on',
        'installer',
        'game_link'
    )

    inlines = [
        IssueReplyInline
    ]

    def game_link(self, obj):
        return mark_safe("<a href='{0}'>{1}<a/>".format(
            reverse("admin:games_game_change", args=(obj.installer.game.id, )),
            obj.installer.game
        ))
    game_link.short_description = "Game (link)"


class GenreAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    ordering = ('name', )


class GameMetadataInline(admin.TabularInline):
    model = models.GameMetadata


class GameLinkAdmin(admin.TabularInline):
    model = models.GameLink


class GameAdmin(admin.ModelAdmin):
    ordering = ("-created", )
    form = forms.BaseGameForm
    list_display = ('__str__', 'is_public', 'year', 'steamid', 'gogslug',
                    'humblestoreid', 'created', 'updated', 'custom_actions')
    list_filter = (GameFilter, 'is_public', 'publisher', 'developer', 'genres')
    list_editable = ('is_public', )
    search_fields = ('name', 'steamid')

    raw_id_fields = ('publisher', 'developer', 'genres', 'platforms', 'change_for')
    autocomplete_lookup_fields = {
        'fk': ['publisher', 'developer'],
        'm2m': ['genres', 'platforms', 'change_for']
    }
    formfield_overrides = {
        BitField: {'widget': BitFieldCheckboxSelectMultiple}
    }
    inlines = [
        GameMetadataInline,
        GameLinkAdmin
    ]
    actions = ['reject_user_suggested_changes']

    def custom_actions(self, game):
        """Column to display additional actions"""

        actions = []

        if game.change_for is not None:
            actions += [self.review_changes_url(game)]
        else:
            change_suggestions_count = models.Game.objects.filter(change_for=game).count()

            if change_suggestions_count > 0:
                actions += [self.list_change_submissions(game, change_suggestions_count)]

        output = ', '.join(actions) if actions else '-'
        return format_html(output)

    def review_changes_url(self, game):
        """Add a link to review the changes of a change submission"""

        url = reverse('admin-change-submission', kwargs={'submission_id': game.id})
        return '<a href="{url}">{text}</a>'.format(url=url, text='Review changes')

    def list_change_submissions(self, game, count):
        """Add a link to review all change suggestions for a given game"""

        url = reverse('admin-change-submissions', kwargs={'game_id': game.id})
        text = '{count} change submission{pl}'.format(count=count, pl='s' if count > 1 else '')
        return '<a href="{url}">{text}</a>'.format(url=url, text=text)

    custom_actions.short_description = 'Actions'


class ScreenshotAdmin(admin.ModelAdmin):
    ordering = ("-uploaded_at", )
    list_display = ("__str__", "game_link", "uploaded_at", "published")
    list_editable = ("published", )
    readonly_fields = ('game_link',)
    search_fields = ['game__name']

    raw_id_fields = ('game', 'uploaded_by')
    autocomplete_lookup_fields = {
        'fk': ['game', 'uploaded_by'],
    }

    def game_link(self, obj):
        return mark_safe("<a href='{0}'>{1}<a/>".format(
            reverse("admin:games_game_change", args=(obj.game.id, )),
            obj.game
        ))

    game_link.short_description = "Game (link)"


class FeaturedAdmin(admin.ModelAdmin):
    list_display = ("__str__", "created_at")


class GameLibraryAdmin(admin.ModelAdmin):
    search_fields = ['user__username']
    raw_id_fields = ('user', 'games')
    autocomplete_lookup_fields = {
        'fk': ['user'],
        'm2m': ['games']
    }


class GameSubmissionAdmin(admin.ModelAdmin):
    list_display = ("game_link", "user_link", "created_at", "accepted_at", 'reason')

    def game_link(self, obj):
        return mark_safe("<a href='{0}'>{1}<a/>".format(
            reverse("admin:games_game_change", args=(obj.game.id, )),
            obj.game
        ))
    game_link.short_description = "Game"

    def user_link(self, obj):
        return mark_safe("<a href='{0}'>{1}</a>".format(
            reverse("admin:accounts_user_change", args=(obj.user.id, )),
            obj.user
        ))
    user_link.short_description = "User"


admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Screenshot, ScreenshotAdmin)
admin.site.register(models.Genre, GenreAdmin)
admin.site.register(models.Company, CompanyAdmin)
admin.site.register(models.Installer, InstallerAdmin)
admin.site.register(models.InstallerIssue, InstallerIssueAdmin)
admin.site.register(models.GameLibrary, GameLibraryAdmin)
admin.site.register(models.Featured, FeaturedAdmin)
admin.site.register(models.GameSubmission, GameSubmissionAdmin)
