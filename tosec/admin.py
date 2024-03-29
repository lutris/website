"""Admin module for TOSEC management"""
from django.contrib import admin

from . import models


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'version', 'author')
    search_fields = ('name', )
    list_filter = ('category', )


class RomInline(admin.StackedInline):
    model = models.TosecRom
    extra = 0


class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'collection')
    search_fields = ('name', )
    list_filter = ('category', 'category__category')
    inlines = [
        RomInline,
    ]


admin.site.register(models.TosecCategory, CategoryAdmin)
admin.site.register(models.TosecGame, GameAdmin)
