from lutrisweb.games.models import Game, Genre, Runner, \
                                   Platform, Company, Installer
from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):

    class Media:
        js = ('/media/js/admin-forms.js',)


class InstallerAdmin(BaseAdmin):
    prepopulated_fields = {'slug': ('game', 'version', )}


class GameAdmin(BaseAdmin):
    prepopulated_fields = {'slug': ('name',)}


class RunnerAdmin(BaseAdmin):
    prepopulated_fields = {'slug': ('name',)}
    

class CompanyAdmin(BaseAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Game, GameAdmin)
admin.site.register(Genre)
admin.site.register(Runner, RunnerAdmin)
admin.site.register(Platform)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Installer, InstallerAdmin)
