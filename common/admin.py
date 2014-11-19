from django.contrib import admin

from common import models
from common import forms


class NewsAdmin(admin.ModelAdmin):
    form = forms.NewsForm
    list_display = ('__unicode__', 'publish_date')
    search_fields = ('title', 'content')


def validate_upload(modeladmin, request, queryset):
    for upload in queryset.all():
        upload.validate()
validate_upload.short_description = "Move uploads to destination"


class UploadAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'destination', 'uploaded_by', 'uploaded_at')
    actions = [validate_upload]


admin.site.register(models.News, NewsAdmin)
admin.site.register(models.Upload, UploadAdmin)
