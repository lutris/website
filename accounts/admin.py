from accounts import models
from django.contrib import admin


class UserAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'email', 'email_confirmed', 'is_staff',
                    'steamid', 'website')
    list_filter = ('is_staff', 'groups')
    search_fields = ('username', 'email')

admin.site.register(models.User, UserAdmin)
