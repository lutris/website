"""Forms for the main app"""
# pylint: disable=W0232, R0903
import os
import yaml

from django import forms
from django.conf import settings
from django.template.defaultfilters import slugify

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django_jcrop.forms import JCropImageWidget
from django_select2.widgets import Select2MultipleWidget, Select2Widget

from games import models


class GameForm(forms.ModelForm):
    title_logo = forms.ImageField(
        widget=JCropImageWidget, required=False
    )

    class Meta:
        model = models.Game
        fields = ('name', 'year', 'website',
                  'platforms', 'genres', 'description', 'title_logo')
        widgets = {
            'platforms': Select2MultipleWidget,
            'genres': Select2MultipleWidget,
        }

    class Media:
        js = (
            settings.STATIC_URL + "/js/jquery.select2.min.js",
        )

    def __init__(self, *args, **kwargs):
        super(GameForm, self).__init__(*args, **kwargs)
        self.fields['platforms'].help_text = ""
        self.fields['genres'].help_text = ""
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', "Submit"))

    def rename_uploaded_file(self, file_field, cleaned_data, slug):
        if self.files.get(file_field):
            clean_field = cleaned_data.get(file_field)
            _, ext = os.path.splitext(clean_field.name)
            relpath = 'games/banners/%s%s' % (slug, ext)
            clean_field.name = relpath
            current_abspath = os.path.join(settings.MEDIA_ROOT, relpath)
            if os.path.exists(current_abspath):
                os.remove(current_abspath)
            return clean_field
        return None

    def clean_name(self):
        name = self.cleaned_data['name']
        slug = slugify(name)
        try:
            game = models.Game.objects.get(slug=slug)
        except models.Game.DoesNotExist:
            return name
        else:
            if game.is_public:
                msg = "This game is already in our database"
            else:
                msg = ("This game has already been submitted, please wait for "
                       "a moderator to publish it.")
            raise forms.ValidationError(msg)

    def clean(self):
        cleaned_data = super(GameForm, self).clean()
        slug = cleaned_data.get('slug', self.instance.slug)
        name = cleaned_data.get('name', self.instance.name)
        if not slug:
            slug = slugify(name)
        # Modify only if title_logo has been posted
        for file_field in ('title_logo', 'icon'):
            cleaned_data[file_field] = self.rename_uploaded_file(file_field,
                                                                 cleaned_data,
                                                                 slug)
        cleaned_data['slug'] = slug
        return cleaned_data


class FeaturedForm(forms.ModelForm):
    class Meta:
        model = models.Featured
        widgets = {
            'image': JCropImageWidget(attrs={'ratio': '3.09'})
        }


class ScreenshotForm(forms.ModelForm):

    class Meta:
        model = models.Screenshot
        fields = ('image', 'description')

    def __init__(self, *args, **kwargs):
        self.game = models.Game.objects.get(pk=kwargs.pop('game_id'))
        super(ScreenshotForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {'class': 'form-horizontal', }
        self.helper.add_input(Submit('submit', "Upload screenshot"))

    def save(self, *args, **kwargs):
        self.instance.game = self.game
        return super(ScreenshotForm, self).save(*args, **kwargs)


class InstallerForm(forms.ModelForm):
    """Form to create and modify installers"""

    class Meta:
        """Form configuration"""
        model = models.Installer
        fields = ('runner', 'version', 'description', 'content')
        widgets = {
            'content': forms.Textarea(
                attrs={'class': 'code-editor', 'spellcheck': 'false'}
            ),
            'runner': Select2Widget,
        }

    def __init__(self, *args, **kwargs):
        super(InstallerForm, self).__init__(*args, **kwargs)
        #self.fields['runner'].empty_label = None

    def clean_content(self):
        """Verify that the content field is valid yaml"""
        yaml_data = self.cleaned_data["content"]
        try:
            yaml_data = yaml.safe_load(yaml_data)
        except yaml.scanner.ScannerError:
            raise forms.ValidationError("Invalid YAML data (scanner error)")
        except yaml.parser.ParserError:
            raise forms.ValidationError("Invalid YAML data (parse error)")
        return yaml.safe_dump(yaml_data, default_flow_style=False)
