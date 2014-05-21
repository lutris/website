from django.contrib import admin

from . import models


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'author')


class RomInline(admin.StackedInline):
    model = models.Rom
    extra = 0


class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    inlines = [
        RomInline,
    ]

admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Game, GameAdmin)
