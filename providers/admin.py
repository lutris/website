"""Admin configuration for providers"""
from django.contrib import admin
from . import models


class ProviderAdmin(admin.ModelAdmin):
    """Admin config for Provider"""
    list_display = ("name", "website")


class ProviderGameAdmin(admin.ModelAdmin):
    """Admin config for ProviderGame"""
    list_display = ("name", "provider")


admin.site.register(models.Provider, ProviderAdmin)
admin.site.register(models.ProviderGame, ProviderGameAdmin)
