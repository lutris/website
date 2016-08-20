from accounts import models
from django.contrib import admin
from django.core import urlresolvers


class UserAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'email', 'email_confirmed', 'is_staff',
                    'steamid', 'website', 'installers_link')
    list_filter = ('is_staff', 'groups')
    search_fields = ('username', 'email')

    def installers_link(self, obj):
        installers_url = urlresolvers.reverse('admin:games_installer_changelist')
        return "<a href='%s?user__id__exact=%s'>Installers</a>" % (
            installers_url, obj.id
        )
    installers_link.allow_tags = True
    installers_link.short_description = 'Installers'

admin.site.register(models.User, UserAdmin)
