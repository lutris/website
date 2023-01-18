"""Admin module for TOSEC management"""
from django.contrib import admin

from . import models


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'author')


class RomInline(admin.StackedInline):
    model = models.TosecRom
    extra = 0


class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name', )
    list_filter = ('category', )
    inlines = [
        RomInline,
    ]


admin.site.register(models.TosecCategory, CategoryAdmin)
admin.site.register(models.TosecGame, GameAdmin)
