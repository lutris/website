from django import forms
from django.utils.text import slugify
from common import models


class AutoSlugForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AutoSlugForm, self).__init__(*args, **kwargs)
        self.fields['slug'].required = False

    def clean(self):
        self.cleaned_data['slug'] = slugify(self.cleaned_data['name'])
        return self.cleaned_data


class NewsForm(forms.ModelForm):

    # pylint: disable=W0232, R0903
    class Meta:
        model = models.News
        fields = ('title', 'content', 'publish_date', 'image', 'user')
