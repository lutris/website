from django.contrib import admin

from common import models
from common import forms


class NewsAdmin(admin.ModelAdmin):
    form = forms.NewsForm
    list_display = ('__unicode__', 'publish_date')
    search_fields = ('title', 'content')


class UploadAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'destination', 'uploaded_by', 'uploaded_at')

admin.site.register(models.News, NewsAdmin)
admin.site.register(models.Upload, UploadAdmin)
