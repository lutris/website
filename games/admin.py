from lutrisweb.games.models import Game, Genre, Runner, Platform, Company, Installer
from django.contrib import admin

admin.site.register(Game)
admin.site.register(Genre)
admin.site.register(Runner)
admin.site.register(Platform)
admin.site.register(Company)
admin.site.register(Installer)

class InstallerAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('game','version',)}
