"""Generic forms"""
from django import forms
from common import models


class NewsForm(forms.ModelForm):
    """Form for editing news"""
    class Meta:
        model = models.News
        fields = ('title', 'content', 'publish_date', 'image', 'user')
