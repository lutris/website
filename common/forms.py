from django import forms
from common import models


class NewsForm(forms.ModelForm):
    class Meta:
        model = models.News
        exclude = ('slug', )
