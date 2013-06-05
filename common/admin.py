from django.contrib import admin

from common import models
from common import forms


class NewsAdmin(admin.ModelAdmin):
    form = forms.NewsForm
    list_display = ('__unicode__', 'publish_date')
    search_fields = ('title', 'content')

admin.site.register(models.SiteACL)
admin.site.register(models.News, NewsAdmin)
