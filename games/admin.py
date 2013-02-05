"""Admin configuration for Lutris games"""
from django.contrib import admin

import models
import forms


class NewsAdmin(admin.ModelAdmin):
    form = forms.NewsForm


class GameAdmin(admin.ModelAdmin):
    form = forms.GameForm
    ordering = ("name", )

    class Media:
        js = ('js/jquery-1.9.0.min.js', )


admin.site.register(models.SiteACL)
admin.site.register(models.News, NewsAdmin)
admin.site.register(models.Game, GameAdmin)
admin.site.register(models.Screenshot)
admin.site.register(models.Genre)
admin.site.register(models.Runner)
admin.site.register(models.Platform)
admin.site.register(models.Company)
admin.site.register(models.Installer)
