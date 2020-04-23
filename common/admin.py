"""Admin configuration for common"""
from django.contrib import admin

from common import models
from common import forms


class NewsAdmin(admin.ModelAdmin):
    """Admin configuration for News"""
    form = forms.NewsForm
    list_display = ('__str__', 'publish_date')
    search_fields = ('title', 'content')


def validate_upload(_modeladmin, _request, queryset):
    """Admin action to validate uploads in a queryset"""
    for upload in queryset.all():
        upload.validate()


validate_upload.short_description = "Move uploads to destination"


class UploadAdmin(admin.ModelAdmin):
    """Admin configuration for Uploads"""
    list_display = ('__str__', 'destination', 'uploaded_by', 'uploaded_at')
    actions = [validate_upload]
    readonly_fields = ['uploaded_by', 'uploaded_at']


admin.site.register(models.News, NewsAdmin)
admin.site.register(models.Upload, UploadAdmin)
