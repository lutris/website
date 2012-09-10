"""Admin configuration for Lutris games"""
from games import models
from django.contrib import admin


admin.site.register(models.News)
admin.site.register(models.Game)
admin.site.register(models.Genre)
admin.site.register(models.Runner)
admin.site.register(models.Platform)
admin.site.register(models.Company)
admin.site.register(models.Installer)
