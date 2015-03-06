from django.contrib import admin
from . import models
from . import forms


class RunnerVersionInline(admin.TabularInline):
    model = models.RunnerVersion


class RunnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'website')
    form = forms.RunnerForm
    inlines = [
        RunnerVersionInline,
    ]

admin.site.register(models.Runner, RunnerAdmin)
