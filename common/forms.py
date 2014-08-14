from django import forms
from django.utils.text import slugify
from common import models


class AutoSlugForm(forms.ModelForm):
    SLUG_LENGTH = 50

    def __init__(self, *args, **kwargs):
        super(AutoSlugForm, self).__init__(*args, **kwargs)
        self.fields['slug'].required = False

    def get_slug(self, name, slug=None):
        if not slug:
            original_slug = slugify(name)[:self.SLUG_LENGTH]
            slug = original_slug
        else:
            original_slug = slug
        slug_exists = True
        counter = 1
        while slug_exists:
            pk = self.instance.pk if self.instance else 0
            slug_exists = (
                self.Meta.model.objects
                .exclude(pk=pk)
                .filter(slug=slug)
                .exists()
            )
            if slug_exists:
                suffix = "-%d" % counter
                slug = original_slug[:self.SLUG_LENGTH - len(suffix)] + suffix
                counter += 1
        return slug

    def clean(self):
        self.cleaned_data['slug'] = self.get_slug(
            self.cleaned_data['name'],
            self.cleaned_data['slug']
        )
        return self.cleaned_data


class NewsForm(forms.ModelForm):

    # pylint: disable=W0232, R0903
    class Meta:
        model = models.News
        fields = ('title', 'content', 'publish_date', 'image', 'user')
