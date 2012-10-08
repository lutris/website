"""Admin configuration for Lutris games"""
from django.contrib import admin

import models
import forms


class GameAdmin(admin.ModelAdmin):
    form = forms.GameForm

    class Media:
        js = ('js/jquery-1.8.2.js', )


admin.site.register(models.SiteACL)
admin.site.register(models.News)
admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Genre)
admin.site.register(models.Runner)
admin.site.register(models.Platform)
admin.site.register(models.Company)
admin.site.register(models.Installer)
