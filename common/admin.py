from django.contrib import admin

from common import models
from common import forms


class NewsAdmin(admin.ModelAdmin):
    form = forms.NewsForm

admin.site.register(models.SiteACL)
admin.site.register(models.News, NewsAdmin)
