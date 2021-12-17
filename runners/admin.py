from django.contrib import admin
from . import models
from . import forms


class RunnerVersionInline(admin.TabularInline):
    model = models.RunnerVersion


class RunnerAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "website")
    form = forms.RunnerForm
    inlines = [RunnerVersionInline]


class RuntimeComponentAdmin(admin.StackedInline):
    model = models.RuntimeComponent
    extra = 0


class RuntimeAdmin(admin.ModelAdmin):
    list_display = ("name", "architecture", "created_at")
    model = models.Runtime

    inlines = [
        RuntimeComponentAdmin,
    ]


admin.site.register(models.Runner, RunnerAdmin)
admin.site.register(models.Runtime, RuntimeAdmin)
