"""Admin configuration for providers"""
from django.contrib import admin
from . import models


class ProviderAdmin(admin.ModelAdmin):
    """Admin config for Provider"""
    list_display = ("name", "website")

class ProviderItemAdmin(admin.ModelAdmin):
    """Generic admin config for Provider models"""
    list_display = ("name", "internal_id", "slug", "provider", "updated_at")
    search_fields = ("internal_id", "name", )
    list_filter = ("provider", )


class ProviderCoverAdmin(admin.ModelAdmin):
    """Admin config for Provider covers"""
    list_display = ("image_id", "game", "provider")
    search_fields = ("image_id", "game")
    list_filter = ("provider", )

admin.site.register(models.Provider, ProviderAdmin)
admin.site.register(models.ProviderGame, ProviderItemAdmin)
admin.site.register(models.ProviderGenre, ProviderItemAdmin)
admin.site.register(models.ProviderPlatform, ProviderItemAdmin)
admin.site.register(models.ProviderCover, ProviderCoverAdmin)
