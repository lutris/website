# pylint: disable=R0201
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from accounts import models


class UserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email', 'email_confirmed', 'is_staff',
                    'steamid', 'website', 'game_count', 'installers_link')
    list_filter = ('is_staff', 'groups')
    search_fields = ('username', 'email', 'steamid')

    def game_count(self, obj):
        return obj.gamelibrary.games.count()

    def installers_link(self, obj):
        installers_url = reverse('admin:games_installer_changelist')
        return mark_safe("<a href='%s?user__id__exact=%s'>Installers</a>" % (
            installers_url, obj.id
        ))
    installers_link.short_description = 'Installers'


admin.site.register(models.User, UserAdmin)
