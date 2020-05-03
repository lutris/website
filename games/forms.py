"""Forms for the main app"""
# pylint: disable=missing-docstring,too-few-public-methods
import os
from datetime import date

import yaml

from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit, ButtonHolder, Fieldset, Field
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django_select2.forms import (
    ModelSelect2Widget,
    Select2MultipleWidget,
    Select2Widget, ModelSelect2MultipleWidget,
)
from bitfield.forms import BitFieldCheckboxSelectMultiple
from croppie.fields import CroppieField

from common.util import get_auto_increment_slug, slugify, load_yaml, dump_yaml
from games import models
from games.util.installer import validate_installer


class AutoSlugForm(forms.ModelForm):

    class Meta:
        # Override this in subclasses. Using a real model here not to confuse pylint
        model = models.Game
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(AutoSlugForm, self).__init__(*args, **kwargs)
        self.fields["slug"].required = False

    def get_slug(self, name, slug=None):
        return get_auto_increment_slug(self.Meta.model, self.instance, name, slug)

    def clean(self):
        self.cleaned_data["slug"] = self.get_slug(
            self.cleaned_data["name"], self.cleaned_data["slug"]
        )
        return self.cleaned_data


class BaseGameForm(AutoSlugForm):
    class Meta:
        model = models.Game
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(BaseGameForm, self).__init__(*args, **kwargs)
        self.fields["gogid"].required = False


class GameForm(forms.ModelForm):
    class Meta:
        model = models.Game
        fields = (
            "name",
            "year",
            "developer",
            "publisher",
            "website",
            "platforms",
            "genres",
            "description",
            "title_logo",
        )
        widgets = {
            "platforms": Select2MultipleWidget,
            "genres": Select2MultipleWidget,
            "developer": ModelSelect2Widget(
                model=models.Company, search_fields=["name__icontains"]
            ),
            "publisher": ModelSelect2Widget(
                model=models.Company, search_fields=["name__icontains"]
            ),
        }

    def __init__(self, *args, **kwargs):
        super(GameForm, self).__init__(*args, **kwargs)
        self.fields["name"].label = "Title"
        self.fields["year"].label = "Release year"
        self.fields["website"].help_text = (
            "The official website (full address). If it doesn't exist, leave blank."
        )
        self.fields["genres"].help_text = ""
        self.fields["description"].help_text = (
            "Copy the official description of the game if you can find "
            "it. Don't write your own. For old games, check Mobygame's Ad "
            "Blurbs, look for the English back cover text."
        )

        self.fields["title_logo"] = CroppieField(
            options={
                "viewport": {"width": 875, "height": 345},
                "boundary": {"width": 875, "height": 345},
                "showZoomer": True,
            }
        )
        self.fields["title_logo"].label = "Upload an image"
        self.fields["title_logo"].help_text = (
            "The banner should include the game's title. "
            "Please make sure that your banner doesn't rely on "
            "transparency as those won't be reflected in the final image"
        )

        self.helper = FormHelper()
        self.helper.include_media = False
        self.helper.layout = Layout(
            Fieldset(
                None,
                "name",
                "year",
                "developer",
                "publisher",
                "website",
                "platforms",
                "genres",
                "description",
                Field("title_logo", template="includes/upload_button.html"),
            ),
            ButtonHolder(Submit("submit", "Submit")),
        )

    def rename_uploaded_file(self, file_field, cleaned_data, slug):
        if self.files.get(file_field):
            clean_field = cleaned_data.get(file_field)
            _, ext = os.path.splitext(clean_field.name)
            relpath = "games/banners/%s%s" % (slug, ext)
            clean_field.name = relpath
            current_abspath = os.path.join(settings.MEDIA_ROOT, relpath)
            if os.path.exists(current_abspath):
                os.remove(current_abspath)
            return clean_field
        return None

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify(name)[:50]

        try:
            game = models.Game.objects.get(slug=slug)
        except models.Game.DoesNotExist:
            return name
        else:
            if game.is_public:
                msg = (
                    "This game is <a href='games/%s'>already in our " "database</a>."
                ) % slug
            else:
                msg = (
                    "This game has <a href='games/%s'>already been "
                    "submitted</a>, you're welcome to nag us so we "
                    "publish it faster."
                ) % slug
            raise forms.ValidationError(mark_safe(msg))


class GameEditForm(forms.ModelForm):
    """Form to suggest changes for games"""

    reason = forms.CharField(
        required=False,
        help_text=(
            "Please describe briefly, why this change is necessary."
            "Please also add sources if applicable."
        ),
    )

    class Meta:
        """Form configuration"""

        model = models.Game
        fields = (
            "name",
            "year",
            "developer",
            "publisher",
            "website",
            "platforms",
            "genres",
            "description",
            "title_logo",
            "reason",
        )

        widgets = {
            "platforms": Select2MultipleWidget,
            "genres": Select2MultipleWidget,
            "developer": ModelSelect2Widget(
                model=models.Company, search_fields=["name__icontains"]
            ),
            "publisher": ModelSelect2Widget(
                model=models.Company, search_fields=["name__icontains"]
            ),
        }

    def __init__(self, payload, *args, **kwargs):
        super(GameEditForm, self).__init__(payload, *args, **kwargs)
        self.fields["name"].label = "Title"
        self.fields["year"].label = "Release year"
        self.fields["title_logo"] = CroppieField(
            options={
                "viewport": {"width": 875, "height": 345},
                "boundary": {"width": 875, "height": 345},
                "showZoomer": True,
                "url": payload["title_logo"].url if payload.get("title_logo") else "",
            }
        )
        self.fields["title_logo"].label = "Upload an image"
        self.fields["title_logo"].required = False

        self.helper = FormHelper()
        self.helper.include_media = False
        self.helper.layout = Layout(
            Fieldset(
                None,
                "name",
                "year",
                "developer",
                "publisher",
                "website",
                "platforms",
                "genres",
                "description",
                Field("title_logo", template="includes/upload_button.html"),
                "reason",
            ),
            ButtonHolder(Submit("submit", "Submit")),
        )

    def clean(self):
        """Overwrite clean to fail validation if unchanged form was submitted"""

        cleaned_data = super(GameEditForm, self).clean()

        # Raise error if nothing actually changed
        if not self.has_changed():
            raise forms.ValidationError("You have not changed anything")

        return cleaned_data


class ScreenshotForm(forms.ModelForm):
    class Meta:
        model = models.Screenshot
        fields = ("image", "description")

    def __init__(self, *args, **kwargs):
        self.game = models.Game.objects.get(pk=kwargs.pop("game_id"))
        super(ScreenshotForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))

    def save(self, commit=True):
        self.instance.game = self.game
        return super(ScreenshotForm, self).save(commit=commit)


class InstallerForm(forms.ModelForm):
    """Form to create and modify installers"""

    class Meta:
        """Form configuration"""

        model = models.Installer
        fields = ("runner", "version", "description", "notes", "content", "draft")
        widgets = {
            "runner": Select2Widget,
            "description": forms.Textarea(attrs={"class": "installer-textarea"}),
            "notes": forms.Textarea(attrs={"class": "installer-textarea"}),
            "content": forms.Textarea(
                attrs={"class": "code-editor", "spellcheck": "false"}
            ),
            "draft": forms.HiddenInput,
        }
        help_texts = {
            "version": (
                "Short version name describing the release of the game "
                "targeted by the installer. It can be the release name (e.g. "
                "GOTY, Gold...) or format (CD...) or platform (Amiga "
                "500...), or the vendor version (e.g. GOG, Steam...) or "
                "the actual software version of the game... Whatever makes "
                "the most sense."
            ),
            "description": (
                "Additional details about the installer. "
                "Do NOT put a description for the game, it will be deleted"
            ),
            "notes": (
                "Describe any known issues or manual tasks required "
                "to run the game properly."
            ),
        }

    def __init__(self, *args, **kwargs):
        super(InstallerForm, self).__init__(*args, **kwargs)
        self.fields["notes"].label = "Technical notes"

    def clean_content(self):
        """Verify that the content field is valid yaml"""
        yaml_data = self.cleaned_data["content"]
        try:
            yaml_data = load_yaml(yaml_data)
        except yaml.error.MarkedYAMLError as ex:
            raise forms.ValidationError(
                "Invalid YAML, problem at line %s, %s"
                % (ex.problem_mark.line, ex.problem)
            )
        return dump_yaml(yaml_data)

    def clean_version(self):
        version = self.cleaned_data["version"]
        if not version:
            raise forms.ValidationError("This field is mandatory")
        if version.lower() == "change me":
            raise forms.ValidationError('When we say "change me", we mean it.')
        if version.lower().endswith("version"):
            raise forms.ValidationError(
                "Don't put 'version' at the end of the 'version' field"
            )
        version_exists = (
            models.Installer.objects.filter(game=self.instance.game, version=version)
            .exclude(id=self.instance.id)
            .count()
        )
        if version_exists:
            raise forms.ValidationError(
                "An installer with the same version name already exists"
            )
        return version

    def clean(self):
        dummy_installer = models.Installer(game=self.instance.game, **self.cleaned_data)
        is_valid, errors = validate_installer(dummy_installer)
        if not is_valid:
            if "content" not in self.errors:
                self.errors["content"] = []
            for error in errors:
                self.errors["content"].append(error)
            raise forms.ValidationError("Invalid installer script")
        # Draft status depends on the submit button clicked
        self.cleaned_data["draft"] = "save" in self.data
        return self.cleaned_data


class InstallerEditForm(InstallerForm):
    """Form to edit an installer"""

    class Meta(InstallerForm.Meta):
        """Form configuration"""

        fields = [
            "runner",
            "version",
            "description",
            "notes",
            "reason",
            "content",
            "draft",
        ]

    reason = forms.CharField(
        widget=forms.Textarea(attrs={"class": "installer-textarea"}),
        required=False,
        help_text="Please describe briefly, why this change is necessary or useful. "
        "This will help us moderate the changes.",
    )


class ForkInstallerForm(forms.ModelForm):
    class Meta:
        model = models.Installer
        fields = ("game",)
        widgets = {
            "game": ModelSelect2Widget(
                model=models.Game, search_fields=["name__icontains"]
            )
        }


class LibraryFilterForm(forms.Form):
    search = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"style": "width: 100%;"}),
        required=False,
    )
    platforms = forms.MultipleChoiceField(
        widget=Select2MultipleWidget(
            attrs={'data-width': '100%',
                   'data-close-on-select': 'false',
                   'data-placeholder': '',
                   'data-minimum-input-length': 3}
        ),
        required=False,
    )
    genres = forms.ModelMultipleChoiceField(
        queryset=models.Genre.objects.all(),
        widget=ModelSelect2MultipleWidget(
            model=models.Genre,
            search_fields=['name__icontains'],
            attrs={'data-width': '100%',
                   'data-close-on-select': 'false',
                   'data-placeholder': '',
                   'data-minimum-input-length': 3}
        ),
        required=False,
    )
    companies = forms.ModelMultipleChoiceField(
        queryset=models.Company.objects.all(),
        widget=ModelSelect2MultipleWidget(
            model=models.Company,
            search_fields=['name__icontains'],
            attrs={'data-width': '100%',
                   'data-close-on-select': 'false',
                   'data-placeholder': '',
                   'data-minimum-input-length': 3}
        ),
        required=False
    )
    years = forms.MultipleChoiceField(
        choices=[(i, i) for i in range(date.today().year, 1970, -1)],
        widget=Select2MultipleWidget(attrs={'data-width': '100%',
                                            'data-close-on-select': 'false',
                                            'data-placeholder': ''}),
        required=False
    )
    flags = forms.MultipleChoiceField(
        choices=models.Game.GAME_FLAGS,
        widget=BitFieldCheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['platforms'].choices = (models.Platform.objects.values_list('pk', 'name'))
