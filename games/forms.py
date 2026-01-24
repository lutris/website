"""Forms for the main app"""

# pylint: disable=missing-docstring,too-few-public-methods
import io
from datetime import date
import json
import logging

import yaml
from PIL import Image
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django_select2.forms import (
    ModelSelect2Widget,
    Select2MultipleWidget,
    Select2Widget,
    ModelSelect2MultipleWidget,
)


from common.util import get_auto_increment_slug, slugify, load_yaml, dump_yaml
from games import models
from games.util.installer import validate_installer

LOGGER = logging.getLogger(__name__)


class AutoSlugForm(forms.ModelForm):
    class Meta:
        # Override this in subclasses. Using a real model here not to confuse pylint
        model = models.Game
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False

    def get_slug(self, name, slug=None):
        return get_auto_increment_slug(self.Meta.model, self.instance, name, slug)

    def clean(self):
        self.cleaned_data["slug"] = self.get_slug(
            self.cleaned_data["name"], self.cleaned_data["slug"]
        )
        return self.cleaned_data


class GameForm(forms.ModelForm):
    crop_data = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = models.Game
        fields = (
            "name",
            "year",
            "platforms",
            "genres",
            "developer",
            "publisher",
            "website",
            "description",
            "title_logo",
        )
        widgets = {
            "name": forms.TextInput(attrs={"class": "select2-lookalike"}),
            "year": forms.TextInput(attrs={"class": "select2-lookalike"}),
            "platforms": Select2MultipleWidget(attrs={"class": "form-control select2"}),
            "genres": Select2MultipleWidget(attrs={"class": "form-control"}),
            "developer": ModelSelect2Widget(
                model=models.Company,
                search_fields=["name__icontains"],
                attrs={"class": "form-control"},
            ),
            "publisher": ModelSelect2Widget(
                model=models.Company,
                search_fields=["name__icontains"],
                attrs={"class": "form-control"},
            ),
            "website": forms.TextInput(attrs={"class": "select2-lookalike"}),
            "description": forms.Textarea(attrs={"class": "select2-lookalike"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify(name)
        if name.endswith(" game"):
            raise forms.ValidationError("Illegal name, do not submit this game.")
        if "geometry dash" in name.lower():
            raise forms.ValidationError(
                "We are warning you. Do not submit Geometry Dash games. We will ban you."
            )
        try:
            models.Game.objects.get(slug=slug)
        except models.Game.DoesNotExist:
            return name
        msg = f"This game is <a href='/games/{slug}'>already in our database</a>."
        raise forms.ValidationError(mark_safe(msg))

    def clean_description(self):
        description = self.cleaned_data["description"]
        if "geometry dash" in description.lower():
            raise forms.ValidationError("We will ban your account if you continue")
        return description

    def clean_website(self):
        website = self.cleaned_data["website"]
        if website.endswith(".io"):
            raise forms.ValidationError(
                ".io websites are not authorized. We will ban your account if you try that again."
            )
        return website

    def process_banner(self, image_data, ratio):
        """Convert image to banner format"""
        if not image_data:
            return None
        image = Image.open(image_data)
        image = image.convert("RGB")
        image = image.crop(ratio)
        image = image.resize((184, 69), Image.LANCZOS)
        image_io = io.BytesIO()
        image.save(image_io, "JPEG")
        return InMemoryUploadedFile(
            image_io,
            "title_logo",
            image_data.name,
            image_data.content_type,
            None,
            None,
        )

    def clean(self):
        """Process banner, which depends on the crop data availability"""
        title_logo = self.cleaned_data.get("title_logo")
        crop_data = self.cleaned_data["crop_data"]
        if crop_data:
            crop_data = json.loads(crop_data)
            crop_points = [int(p) for p in crop_data["points"]]
            try:
                self.cleaned_data["title_logo"] = self.process_banner(
                    title_logo, crop_points
                )
            except AttributeError as ex:
                LOGGER.warning(ex)
                raise forms.ValidationError("This is not a valid image format: %s" % ex)
        return self.cleaned_data


class GameEditForm(GameForm):
    """Form to suggest changes for games"""

    crop_data = forms.CharField(required=False, widget=forms.HiddenInput())
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
            "name": forms.TextInput(attrs={"class": "select2-lookalike"}),
            "year": forms.TextInput(attrs={"class": "select2-lookalike"}),
            "website": forms.TextInput(attrs={"class": "select2-lookalike"}),
            "description": forms.Textarea(attrs={"class": "select2-lookalike"}),
            "platforms": Select2MultipleWidget(attrs={"style": "width: 100%;"}),
            "genres": Select2MultipleWidget(attrs={"style": "width: 100%;"}),
            "developer": ModelSelect2Widget(
                model=models.Company,
                search_fields=["name__icontains"],
                attrs={"style": "width: 100%;"},
            ),
            "publisher": ModelSelect2Widget(
                model=models.Company,
                search_fields=["name__icontains"],
                attrs={"style": "width: 100%;"},
            ),
        }

    def __init__(self, payload, *args, **kwargs):
        super().__init__(payload, *args, **kwargs)
        self.fields["title_logo"].required = False
        self.fields["reason"].widget = forms.TextInput(
            attrs={"class": "select2-lookalike"}
        )

    def clean_name(self):
        return self.cleaned_data["name"]

    def clean(self):
        """Overwrite clean to fail validation if unchanged form was submitted"""
        # Raise error if nothing actually changed
        if not self.has_changed():
            raise forms.ValidationError("You have not changed anything")
        return super().clean()


class ScreenshotForm(forms.ModelForm):
    class Meta:
        model = models.Screenshot
        fields = ("image", "description")

    def __init__(self, *args, **kwargs):
        self.game = models.Game.objects.get(pk=kwargs.pop("game_id"))
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.game = self.game
        return super().save(commit=commit)


class InstallerForm(forms.ModelForm):
    """Form to create and modify installers"""

    class Meta:
        """Form configuration"""

        model = models.InstallerDraft
        fields = (
            "runner",
            "version",
            "description",
            "notes",
            "credits",
            "content",
            "draft",
        )
        widgets = {
            "runner": Select2Widget,
            "description": forms.TextInput(
                attrs={"style": "width: 100%;", "class": "select2-lookalike"}
            ),
            "notes": forms.Textarea(attrs={"class": "installer-textarea"}),
            "credits": forms.Textarea(attrs={"class": "installer-textarea"}),
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
                "Optional information about the installer."
                "This is not meant for the game description "
                "or to summarize your changes."
                "If unsure, please leave this field empty."
            ),
            "notes": (
                "Describe any known issues or manual tasks required "
                "to run the game properly."
            ),
            "credits": (
                "You can optionally provide credits for the installers or the software used in it."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notes"].label = "Technical notes"

    def clean_description(self):
        """Remove HTML tags from the description"""
        if self.cleaned_data["description"]:
            return strip_tags(self.cleaned_data["description"])
        return ""

    def clean_notes(self):
        """Remove HTML tags from the description"""
        if self.cleaned_data["notes"]:
            return strip_tags(self.cleaned_data["notes"])
        return ""

    def clean_content(self):
        """Verify that the content field is valid yaml"""
        yaml_data = self.cleaned_data["content"]
        try:
            yaml_data = load_yaml(yaml_data)
        except yaml.error.MarkedYAMLError as ex:
            raise forms.ValidationError(
                f"Invalid YAML, problem at line {ex.problem_mark.line}, {ex.problem}"
            )
        if "script" in yaml_data:
            yaml_data = yaml_data["script"]
        return dump_yaml(yaml_data)

    def clean_version(self):
        version = self.cleaned_data["version"]
        if not version:
            raise forms.ValidationError("This field is mandatory")
        if version.lower().endswith("version"):
            raise forms.ValidationError(
                "Don't put 'version' at the end of the 'version' field"
            )
        if self.instance.base_installer:
            version_exists = (
                models.Installer.objects.filter(
                    game=self.instance.game, version=version
                )
                .exclude(id=self.instance.base_installer.id)
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
            "credits",
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
    q = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={"style": "width: 100%;", "class": "select2-lookalike"}
        ),
        required=False,
        label="Search",
    )
    platforms = forms.MultipleChoiceField(
        widget=Select2MultipleWidget(
            attrs={
                "data-width": "100%",
                "data-close-on-select": "false",
                "data-placeholder": "",
                "data-minimum-input-length": 2,
            }
        ),
        required=False,
    )
    genres = forms.ModelMultipleChoiceField(
        queryset=models.Genre.objects.all(),
        widget=ModelSelect2MultipleWidget(
            model=models.Genre,
            search_fields=["name__icontains"],
            attrs={
                "data-width": "100%",
                "data-close-on-select": "false",
                "data-placeholder": "",
                "data-minimum-input-length": 3,
            },
        ),
        required=False,
    )
    companies = forms.ModelMultipleChoiceField(
        queryset=models.Company.objects.all(),
        widget=ModelSelect2MultipleWidget(
            model=models.Company,
            search_fields=["name__icontains"],
            attrs={
                "data-width": "100%",
                "data-close-on-select": "false",
                "data-placeholder": "",
                "data-minimum-input-length": 3,
            },
        ),
        required=False,
    )
    years = forms.MultipleChoiceField(
        choices=[(i, i) for i in range(date.today().year, 1970, -1)],
        widget=Select2MultipleWidget(
            attrs={
                "data-width": "100%",
                "data-close-on-select": "false",
                "data-placeholder": "",
            }
        ),
        required=False,
    )
    SEARCH_FLAGS = (
        ("open_source", "Open source"),
        ("free", "Free"),
    )
    flags = forms.MultipleChoiceField(
        choices=SEARCH_FLAGS,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "checkbox-list"}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["platforms"].choices = models.Platform.objects.values_list(
            "pk", "name"
        )


class GameMergeSuggestionForm(forms.Form):
    other_game_slug = forms.CharField(
        max_length=255,
        label="Game to merge (slug or URL)",
        help_text="Enter the slug or full URL of the duplicate game.",
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        label="Reason",
        help_text="Explain why these games should be merged.",
    )

    def clean_other_game_slug(self):
        value = self.cleaned_data["other_game_slug"].strip().rstrip("/")
        # Extract slug from a full URL like https://lutris.net/games/some-game/
        if "/" in value:
            value = value.split("/")[-1]
        if not value:
            raise forms.ValidationError("Please enter a valid game slug or URL.")
        try:
            game = models.Game.objects.get(slug=value)
        except models.Game.DoesNotExist:
            raise forms.ValidationError("No game found with slug '%s'." % value)
        return game
