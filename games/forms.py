"""Forms for the main app"""
# pylint: disable=W0232, R0903
import os
from collections import OrderedDict

import yaml
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django_select2.forms import (HeavySelect2Widget, ModelSelect2Widget,
                                  Select2MultipleWidget, Select2Widget)

from common.util import get_auto_increment_slug
from games import models
from games.util.installer import validate_installer


class AutoSlugForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(AutoSlugForm, self).__init__(*args, **kwargs)
        self.fields['slug'].required = False

    def get_slug(self, name, slug=None):
        return get_auto_increment_slug(self.Meta.model,
                                       self.instance, name, slug)

    def clean(self):
        self.cleaned_data['slug'] = self.get_slug(
            self.cleaned_data['name'],
            self.cleaned_data['slug']
        )
        return self.cleaned_data


class BaseGameForm(AutoSlugForm):
    class Meta:
        model = models.Game
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(BaseGameForm, self).__init__(*args, **kwargs)
        self.fields['gogid'].required = False


class GameForm(forms.ModelForm):
    class Meta(object):
        model = models.Game
        fields = ('name', 'year', 'website',
                  'platforms', 'genres', 'description', 'title_logo')
        widgets = {
            'platforms': Select2MultipleWidget,
            'genres': Select2MultipleWidget
        }

    def __init__(self, *args, **kwargs):
        super(GameForm, self).__init__(*args, **kwargs)

        self.fields['search'] = forms.CharField(
            widget=HeavySelect2Widget(
                data_view='tgd.search_json'
            ),
            required=False,
            label="Search on TheGamesDB.net"
        )

        self.fields['name'].label = "Title"
        self.fields['year'].label = "Release year"
        self.fields['website'].help_text = (
            "The official website (full address). If it doesn't exist, leave "
            "blank."
        )
        self.fields['platforms'].help_text = (
            "Only select platforms expected to have an installer, "
            "not all platforms the game was released for. <br/>"
            "<strong class='obnoxious-warning'>Do not add Windows "
            "for games with a native version unless there is a very good reason to!"
            "</strong>"
        )
        self.fields['genres'].help_text = ""
        self.fields['description'].help_text = (
            "Copy the official description of the game if you can find "
            "it. Don't write your own. For old games, check Mobygame's Ad "
            "Blurbs, look for the English back cover text."
        )
        self.fields['title_logo'].label = "Banner icon"
        self.fields['title_logo'].help_text = (
            "The banner should include the full title in readable size (big). "
            "You'll be able to crop the uploaded image to the right format. "
            "The image will be converted to JPG (no transparency). "
            "If you can't make a good banner, don't worry. Somebody will "
            "eventually make a better one. Probably."
        )

        fields_order = [
            'search', 'name', 'year', 'website', 'platforms', 'genres', 'description', 'title_logo'
        ]
        self.fields = OrderedDict((k, self.fields[k]) for k in fields_order)

        self.helper = FormHelper()
        self.helper.include_media = False
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
        slug = slugify(name)[:50]

        try:
            game = models.Game.objects.get(slug=slug)
        except models.Game.DoesNotExist:
            return name
        else:
            if game.is_public:
                msg = ("This game is <a href='games/%s'>already in our "
                       "database</a>.") % slug
            else:
                msg = ("This game has <a href='games/%s'>already been "
                       "submitted</a>, you're welcome to nag us so we "
                       "publish it faster.") % slug
            raise forms.ValidationError(mark_safe(msg))


class GameEditForm(forms.ModelForm):
    """Form to suggest changes for games"""

    reason = forms.CharField(
        required=False,
        help_text=(
            'Please describe briefly, why this change is necessary.'
            'Please also add sources if applicable.'
        )
    )

    class Meta(object):
        """Form configuration"""

        model = models.Game
        fields = ('name', 'year', 'website', 'platforms', 'genres', 'description', 'reason')
        widgets = {
            'platforms': Select2MultipleWidget,
            'genres': Select2MultipleWidget
        }

    def __init__(self, *args, **kwargs):
        super(GameEditForm, self).__init__(*args, **kwargs)

        self.fields['name'].label = 'Title'
        self.fields['year'].label = 'Release year'

        fields_order = [
            'name', 'year', 'website', 'platforms', 'genres', 'description', 'reason'
        ]
        self.fields = OrderedDict((k, self.fields[k]) for k in fields_order)

        self.helper = FormHelper()
        self.helper.include_media = False
        self.helper.add_input(Submit('submit', 'Submit'))

    def clean(self):
        """Overwrite clean to fail validation if unchanged form was submitted"""

        cleaned_data = super(GameEditForm, self).clean()

        # Raise error if nothing actually changed
        if not self.has_changed():
            raise forms.ValidationError('You have not changed anything')

        return cleaned_data


class FeaturedForm(forms.ModelForm):
    class Meta:
        model = models.Featured
        exclude = ()


class ScreenshotForm(forms.ModelForm):
    class Meta(object):
        model = models.Screenshot
        fields = ('image', 'description')

    def __init__(self, *args, **kwargs):
        self.game = models.Game.objects.get(pk=kwargs.pop('game_id'))
        super(ScreenshotForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', "Submit"))

    def save(self, *args, **kwargs):
        self.instance.game = self.game
        return super(ScreenshotForm, self).save(*args, **kwargs)


class InstallerForm(forms.ModelForm):
    """Form to create and modify installers"""

    class Meta:
        """Form configuration"""
        model = models.Installer
        fields = ('runner', 'version', 'description', 'notes', 'content', 'draft')
        widgets = {
            'runner': Select2Widget,
            'description': forms.Textarea(
                attrs={'class': 'installer-textarea'}
            ),
            'notes': forms.Textarea(attrs={'class': 'installer-textarea'}),
            'content': forms.Textarea(
                attrs={'class': 'code-editor', 'spellcheck': 'false'}
            ),
            'draft': forms.HiddenInput
        }
        help_texts = {
            'version': (
                "Short version name describing the release of the game "
                "targeted by the installer. It can be the release name (e.g. "
                "GOTY, Gold...) or format (CD...) or platform (Amiga "
                "500...), or the vendor version (e.g. GOG, Steam...) or "
                "the actual software version of the game... Whatever makes "
                "the most sense."
            ),
            'description': ("Additional details about the installer. "
                            "Do NOT put a description for the game, it will be deleted"),
            'notes': ("Describe any known issues or manual tasks required "
                      "to run the game properly."),
        }

    def __init__(self, *args, **kwargs):
        super(InstallerForm, self).__init__(*args, **kwargs)
        self.fields['notes'].label = "Technical notes"

    def clean_content(self):
        """Verify that the content field is valid yaml"""
        yaml_data = self.cleaned_data["content"]
        try:
            yaml_data = yaml.safe_load(yaml_data)
        except yaml.scanner.ScannerError:
            raise forms.ValidationError("Invalid YAML data (scanner error)")
        except yaml.parser.ParserError:
            raise forms.ValidationError("Invalid YAML data (parse error)")
        except yaml.composer.ComposerError as ex:
            raise forms.ValidationError(
                "Script error: %s."
                "Make sure to quote any string with special characters such as '*' or ':'"
                % ex.problem
            )
        return yaml.safe_dump(yaml_data, default_flow_style=False)

    def clean_version(self):
        version = self.cleaned_data['version']
        if not version:
            raise forms.ValidationError('This field is mandatory')
        if version.lower() == 'change me':
            raise forms.ValidationError('When we say "change me", we mean it.')
        if version.lower().endswith('version'):
            raise forms.ValidationError("Don't put 'version' at the end of the 'version' field")
        return version

    def clean(self):
        dummy_installer = models.Installer(game=self.instance.game,
                                           **self.cleaned_data)
        is_valid, errors = validate_installer(dummy_installer)
        if not is_valid:
            if 'content' not in self.errors:
                self.errors['content'] = []
            for error in errors:
                self.errors['content'].append(error)
            raise forms.ValidationError("Invalid installer script")
        else:
            # Draft status depends on the submit button clicked
            self.cleaned_data['draft'] = 'save' in self.data
            return self.cleaned_data


class InstallerEditForm(InstallerForm):
    """Form to edit an installer"""

    class Meta(InstallerForm.Meta):
        """Form configuration"""

        fields = ['runner', 'version', 'description', 'notes', 'reason',
                  'content', 'draft']

    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'installer-textarea'}),
        required=False,
        help_text='Please describe briefly, why this change is necessary or useful. '
                  'This will help us moderate the changes.'
    )

    def __init__(self, *args, **kwargs):
        super(InstallerEditForm, self).__init__(*args, **kwargs)


class ForkInstallerForm(forms.ModelForm):

    class Meta:
        model = models.Installer
        fields = ('game', )
        widgets = {
            'game': ModelSelect2Widget(
                model=models.Game,
                search_fields=['name__icontains']
            )
        }
