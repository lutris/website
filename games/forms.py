"""Forms for the main app"""
# pylint: disable=W0232, R0903
import os
import yaml

from django import forms
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from games import models
from games.util.installer import ScriptValidator


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


class BaseGameForm(AutoSlugForm):
    class Meta:
        model = models.Game
        fields = '__all__'


class GameForm(forms.ModelForm):
    class Meta(object):
        model = models.Game
        fields = ('name', 'year', 'website',
                  'platforms', 'genres', 'description', 'title_logo')

    def __init__(self, *args, **kwargs):
        super(GameForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Title"
        self.fields['year'].label = "Release year"
        self.fields['website'].help_text = (
            "The official website. If it doesn't exist, leave blank."
        )
        self.fields['platforms'].help_text = (
            "Only select platforms expected to have an installer, "
            "not all platforms the game was released on. For example, Windows "
            "is not needed for Linux native games."
        )
        self.fields['genres'].help_text = ""
        self.fields['description'].help_text = (
            "Copy the official description of the game if you can find "
            "it. Don't write your own."
        )
        self.fields['title_logo'].label = "Banner icon"
        self.fields['title_logo'].help_text = (
            "The banner should include the full title in readable size (big). "
            "You'll be able to crop the uploaded image to the right format. "
            "The image format is JPG, so no transparency. "
            "If you can't make a good banner, don't worry. Somebody will "
            "eventually make a better one. Probably."
        )
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
                msg = ("This game is <a href='games/%s'>already in our "
                       "database</a>.") % slug
            else:
                msg = ("This game has <a href='games/%s'>already been "
                       "submitted</a>, you're welcome to nag us so we "
                       "publish it faster.") % slug
            raise forms.ValidationError(mark_safe(msg))


class FeaturedForm(forms.ModelForm):
    class Meta:
        model = models.Featured


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
        fields = ('runner', 'version', 'description', 'notes', 'content')
        widgets = {
            'description': forms.Textarea(
                attrs={'class': 'installer-textarea'}
                ),
            'notes': forms.Textarea(attrs={'class': 'installer-textarea'}),
            'content': forms.Textarea(
                attrs={'class': 'code-editor', 'spellcheck': 'false'}
            )
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
            'description': "Additionnal details.",
            'notes': ("Describe any known issues or manual tasks required "
                      "to run the game properly."),
        }

    def __init__(self, *args, **kwargs):
        super(InstallerForm, self).__init__(*args, **kwargs)
        self.fields['notes'].label = "Technical notes"

    def clean_version(self):
        version = self.cleaned_data['version']
        slug = self.instance.build_slug(version)
        installer_exists = (models.Installer.objects
                            .filter(slug=slug)
                            .exclude(pk=self.instance.pk)
                            .exists())
        if installer_exists:
            message = u"Installer for this version already exists"
            raise forms.ValidationError(message)
        return version

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

    def clean(self):
        dummy_installer = models.Installer(game=self.instance.game,
                                           **self.cleaned_data)
        validator = ScriptValidator(dummy_installer.as_dict())
        if not validator.is_valid():
            if 'content' not in self.errors:
                self.errors['content'] = []
            for error in validator.errors:
                self.errors['content'].append(error)
            raise forms.ValidationError("Invalid installer script")
        else:
            return self.cleaned_data


class RunnerForm(AutoSlugForm):

    class Meta:
        model = models.Runner
        fields = '__all__'
