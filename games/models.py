"""Models for main lutris app"""
# pylint: disable=no-member,too-few-public-methods,too-many-lines,consider-using-f-string
import os
import shutil
import datetime
import json
import logging
import random
import re
from collections import defaultdict
from itertools import chain

import six
import yaml
import reversion
from reversion.models import Version, Revision
from bitfield import BitField
from sorl.thumbnail import get_thumbnail
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Count, Q
from django.urls import reverse

from common.util import get_auto_increment_slug, slugify, load_yaml, dump_yaml
from emails import messages
from games.util import steam, gog
from platforms.models import Platform
from runners.models import Runner
from providers.models import ProviderGame

LOGGER = logging.getLogger(__name__)
DEFAULT_INSTALLER = {
    "files": [{"file_id": "http://location"}, {"unredistribuable_file": "N/A"}],
    "installer": [{"move": {"src": "file_id", "dst": "$GAMEDIR"}}],
}


class Company(models.Model):
    """Gaming company"""

    name = models.CharField(max_length=127)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to="companies/logos", blank=True)
    website = models.CharField(max_length=128, blank=True)

    class Meta:
        """Additional configuration for model"""

        verbose_name_plural = "companies"
        ordering = ["name"]

    def get_absolute_url(self):
        """Return URL to a company's games"""
        return reverse("games_by_company", kwargs={'company': self.pk})

    def __str__(self):
        return str(self.name)

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.name:
            self.slug = slugify(self.name)
        if not self.slug:
            raise ValueError("Tried to save Company without a slug: %s" % self)
        return super(Company, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    @staticmethod
    def autocomplete_search_fields():
        """Autocomplete fields used in the Django admin"""
        return ("name__icontains", "slug__icontains")


class GenreManager(models.Manager):
    """Model manager for Genre"""

    def with_games(self):
        """Query genres that have games assigned to them"""
        genre_list = (
            Game.objects.with_installer()
            .values_list("genres")
            .annotate(g_count=Count("genres"))
            .filter(g_count__gt=0)
        )
        genre_ids = [genre[0] for genre in genre_list]
        return self.get_queryset().filter(id__in=genre_ids)


class Genre(models.Model):
    """Gaming genre"""

    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    objects = GenreManager()

    class Meta:
        """Model configuration"""
        ordering = ["name"]

    def __str__(self):
        return str(self.name)

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Genre, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    @staticmethod
    def autocomplete_search_fields():
        """Autocomplete fields used in the Django admin"""
        return ("name__icontains",)


class GameManager(models.Manager):
    """Model manager for Game"""

    class Meta:
        """Model configuration"""
        ordering = ["name"]

    def published(self):
        """Query games that are published"""
        return self.get_queryset().filter(change_for__isnull=True, is_public=True)

    def with_installer(self):
        """Query games that have an installer"""
        return (
            self.get_queryset()
            .filter(change_for__isnull=True)
            .filter(is_public=True)
            .filter(
                Q(installers__published=True)
                | Q(platforms__default_installer__startswith="{")
            )
            .order_by("name")
            .annotate(installer_count=Count("installers", distinct=True))
        )

    def get_random(self, option=""):
        """Return a random game"""
        if not re.match(r"^[\w\d-]+$", option) or len(option) > 128:
            return None
        pk_query = self.get_queryset()
        if option == "incomplete":
            pk_query = pk_query.filter(change_for__isnull=True, year=None)
        elif option == "published":
            pk_query = self.with_installer()
        elif len(option) > 1:
            pk_query = pk_query.filter(
                Q(platforms__slug=option) | Q(installers__runner__slug=option)
            )
        pks = pk_query.values_list("pk", flat=True)
        if not pks:
            return None
        random_pk = random.choice(pks)
        return self.get_queryset().get(pk=random_pk)


class Game(models.Model):
    """Game model"""

    GAME_FLAGS = (
        ("fully_libre", "Fully libre"),
        ("open_engine", "Open engine only"),
        ("free", "Free"),
        ("freetoplay", "Free-to-play"),
        ("pwyw", "Pay what you want"),
        ("protected", "Installer modification is restricted"),
    )

    # These model fields are editable by the user
    TRACKED_FIELDS = [
        "name", "year", "platforms", "genres", "publisher", "developer",
        "website", "description", "title_logo"
    ]

    ICON_PATH = os.path.join(settings.MEDIA_ROOT, "game-icons/128")
    BANNER_PATH = os.path.join(settings.MEDIA_ROOT, "game-banners/184")

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    platforms = models.ManyToManyField(Platform, blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    publisher = models.ForeignKey(
        Company,
        related_name="published_game",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    developer = models.ForeignKey(
        Company,
        related_name="developed_game",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    website = models.CharField(max_length=200, blank=True)
    icon = models.ImageField(upload_to="uploads/icons", blank=True)
    title_logo = models.ImageField(upload_to="uploads/banners", blank=True)
    description = models.TextField(blank=True)
    is_public = models.BooleanField("Published", default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    steamid = models.PositiveIntegerField(null=True, blank=True)
    gogslug = models.CharField(max_length=200, blank=True)
    gogid = models.PositiveIntegerField(null=True, blank=True)
    humblestoreid = models.CharField(max_length=200, blank=True)
    flags = BitField(flags=GAME_FLAGS)
    popularity = models.IntegerField(default=0)
    provider_games = models.ManyToManyField(ProviderGame, related_name="games", blank=True)

    # Indicates whether this data row is a changeset for another data row.
    # If so, this attribute is not NULL and the value is the ID of the
    # corresponding data row
    change_for = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE
    )

    objects = GameManager()

    class Meta:
        """Model configuration"""
        ordering = ["name"]
        permissions = (("can_publish_game", "Can publish game"),)

    @classmethod
    def valid_fields(cls):
        """Return a list of valid field names for the model"""
        return [f.name for f in cls._meta.fields]

    def __str__(self):
        if self.change_for is None:
            return self.name
        return "[Changes for] " + self.change_for.name

    @staticmethod
    def autocomplete_search_fields():
        """Autocomplete fields used in the Django admin"""
        return ("name__icontains",)

    @property
    def humbleid(self):
        """Humble Bundle ID, different from humblestoreid (store page ID for Humble Bundle)
        This should really get deprecated.
        """
        _slugs = self.provider_games.filter(
            provider__name="humblebundle"
        ).values_list("slug", flat=True)
        if _slugs:
            return _slugs[0]
        return ""

    @property
    def user_count(self):
        """How many users have the game in their libraries"""
        return self.libraries.count()

    @property
    def website_url(self):
        """Returns self.website guaranteed to be a valid URI"""
        if not self.website:
            return None

        # Fall back to http if no protocol specified (cannot assume that https will work)
        has_protocol = "://" in self.website
        return "http://" + self.website if not has_protocol else self.website

    @property
    def website_url_hr(self):
        """Returns a human readable website URL (stripped protocols and trailing slashes)"""
        if not self.website:
            return None
        return self.website.split("https:", 1)[-1].split("http:", 1)[-1].strip("/")

    @property
    def banner_url(self):
        """Return URL for the game banner"""
        if self.title_logo:
            # Hardcoded domain isn't ideal but we have to find another solution for storing
            # and referencing banners and icons anyway so this will do for the time being.
            return settings.ROOT_URL + reverse("get_banner", kwargs={"slug": self.slug})
        return ""

    @property
    def icon_url(self):
        """Return URL for the game icon"""
        if self.icon:
            return settings.ROOT_URL + reverse("get_icon", kwargs={"slug": self.slug})
        return ""

    @property
    def flag_labels(self):
        """Return labels of active flags, suitable for display"""
        # pylint: disable=E1133; self.flags *is* iterable
        return [self.flags.get_label(flag[0]) for flag in self.flags if flag[1]]

    @property
    def submission(self):
        """Return the first (and only) submission for a game"""
        return self.submissions.first()

    def get_change_model(self):
        """Returns a dictionary which can be used as initial value in forms"""
        return {
            "name": self.name,
            "year": self.year,
            "platforms": [x.id for x in list(self.platforms.all())],
            "genres": [x.id for x in list(self.genres.all())],

            # The Select2 dropdowns want ids instead of complete models
            "publisher": self.publisher.id if self.publisher else None,
            "developer": self.developer.id if self.developer else None,

            "website": self.website,
            "description": self.description,
            "title_logo": self.title_logo,
        }

    def get_changes(self):
        """Returns a dictionary of the changes"""

        changes = []

        # From the considered fields, only those who differ will be returned
        for entry in self.TRACKED_FIELDS:
            old_value = getattr(self.change_for, entry)
            new_value = getattr(self, entry)

            # M2M relations to string
            if entry in ["platforms", "genres"]:
                old_value = ", ".join(
                    "[{0}]".format(str(x)) for x in list(old_value.all())
                )
                new_value = ", ".join(
                    "[{0}]".format(str(x)) for x in list(new_value.all())
                )

            if old_value != new_value:
                changes.append((entry, old_value, new_value))

        return changes

    def apply_changes(self, change_set):
        """Applies user-suggested changes to this model"""

        self.name = change_set.name
        self.year = change_set.year
        self.platforms.set(change_set.platforms.all())
        self.genres.set(change_set.genres.all())
        self.publisher = change_set.publisher
        self.developer = change_set.developer
        self.website = change_set.website
        self.description = change_set.description
        self.title_logo = change_set.title_logo

    def merge_with_game(self, other_game):
        """Merge the information of another game into this game.
        This is a destructive operation the other game gets deleted
        after the merge is done.
        """
        # Move screenshots
        for screenshot in other_game.screenshot_set.all():
            screenshot.game = self
            screenshot.save()

        # Move installers
        for installer in other_game.installers.all():
            installer.game = self
            installer.save()

        # Move aliases
        for alias in other_game.aliases.all():
            alias.game = self
            alias.save()

        # Create a new alias from the other game
        GameAlias.objects.create(
            game=self,
            name=other_game.name,
            slug=other_game.slug
        )

        # Merge genres
        for genre in other_game.genres.all():
            self.genres.add(genre)

        # Merge platforms
        for platform in other_game.platforms.all():
            self.platforms.add(platform)

        # Move user libraries
        for library in other_game.libraries.all():
            library.games.add(self)

        # Move provider games
        for provider_game in other_game.provider_games.all():
            self.provider_games.add(provider_game)

        # Merge Steam ID if none is present
        if not self.steamid:
            self.steamid = other_game.steamid

        # Merge year if none is provided
        if not self.year:
            self.year = other_game.year

        # Merge icon if none exist
        if not self.icon:
            self.icon = other_game.icon

        # Merge banner if there is none
        if not self.title_logo:
            self.title_logo = other_game.title_logo

        # Merge weblinks
        for link in other_game.links.all():
            link.game = self
            link.save()

        # Merge publisher
        if not self.publisher:
            self.publisher = other_game.publisher

        # Merge developer
        if not self.developer:
            self.developer = other_game.developer

        # Merge website
        if not self.website:
            self.website = other_game.website

        # Merge description
        if not self.description:
            self.description = other_game.description

        # Delete game
        delete_results = other_game.delete()
        LOGGER.info("Merged and deleted game: %s", delete_results)

    def has_installer(self):
        """Return whether this game has an installer"""
        return self.installers.exists() or self.has_auto_installers()

    def has_auto_installers(self):
        """Return whether this game has auto-generated installers"""
        return self.platforms.filter(default_installer__isnull=False).exists()

    def get_absolute_url(self):
        """Return the absolute url for a game"""
        if self.change_for:
            slug = self.change_for.slug
        else:
            slug = self.slug
        return reverse("game_detail", kwargs={"slug": slug})

    def precache_media(self):
        """Prerenders thumbnails so we can host them as static files"""
        icon_path = os.path.join(settings.MEDIA_ROOT, self.icon.name)
        if self.icon.name and os.path.exists(icon_path):
            self.precache_icon()
        banner_path = os.path.join(settings.MEDIA_ROOT, self.title_logo.name)
        if self.title_logo.name and os.path.exists(banner_path):
            self.precache_banner()

    def precache_icon(self):
        """Render the icon and place it in the icons folder"""
        dest_file = os.path.join(self.ICON_PATH, "%s.png" % self.slug)
        if os.path.exists(dest_file):
            return
        thumbnail = get_thumbnail(
            self.icon,
            settings.ICON_SIZE,
            crop="center",
            format="PNG"
        )
        shutil.copy(os.path.join(settings.MEDIA_ROOT, thumbnail.name), dest_file)

    def precache_banner(self):
        """Render the icon and place it in the banners folder"""
        dest_file = os.path.join(self.BANNER_PATH, "%s.jpg" % self.slug)
        if os.path.exists(dest_file):
            return
        thumbnail = get_thumbnail(
            self.title_logo,
            settings.BANNER_SIZE,
            crop="center"
        )
        shutil.copy(os.path.join(settings.MEDIA_ROOT, thumbnail.name), dest_file)

    def set_logo_from_steam(self):
        """Fetch the banner from Steam and use it for the game"""
        if self.title_logo or not self.steamid:
            return
        self.title_logo = ContentFile(
            steam.get_capsule(self.steamid), "%s.jpg" % self.steamid
        )

    def set_logo_from_steam_api(self, img_url):
        """Sets the game banner from the Steam API URLs"""
        self.title_logo = ContentFile(
            steam.get_image(self.steamid, img_url), "%s.jpg" % self.steamid
        )

    def set_icon_from_steam_api(self, img_url):
        """Sets the game icon from the Steam API URLs"""
        self.icon = ContentFile(
            steam.get_image(self.steamid, img_url), "%s.jpg" % self.steamid
        )

    def set_logo_from_gog(self, gog_game):
        """Sets the game logo from the data retrieved from GOG"""
        if self.title_logo or not self.gogid:
            return
        self.title_logo = ContentFile(
            gog.get_logo(gog_game), "gog-%s.jpg" % self.gogid
        )

    def steam_support(self):
        """ Return the platform supported by Steam """
        if not self.steamid:
            return False
        platforms = [p.slug for p in self.platforms.all()]
        if "linux" in platforms:
            return "linux"
        if "windows" in platforms:
            return "windows"
        return True

    def get_default_installers(self):
        """Return all auto-installers for this game's platforms"""
        auto_installers = []

        for platform in self.platforms.all():
            if platform.default_installer:
                installer = platform.default_installer
                installer["name"] = self.name
                installer["game_slug"] = self.slug
                installer["version"] = platform.name
                installer["slug"] = "-".join((self.slug[:30], platform.slug[:20]))
                installer["platform"] = platform.slug
                installer["description"] = ""
                installer["published"] = True
                installer["auto"] = True
                auto_installers.append(installer)
        return auto_installers

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # Only create slug etc. if this is a game submission, no change submission
        if not self.change_for:
            if not self.slug:
                self.slug = slugify(self.name)[:50]
            if not self.slug:
                raise ValueError("Can't generate a slug for name %s" % self.name)
            self.set_logo_from_steam()
        super(Game, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        # Not ideal to have this here since this can generate disk IO activity
        # Not a problem though, we want to discourage mass updates for games
        # since that would DDOS the site.
        try:
            self.precache_media()
        except Exception as ex:  # pylint: disable=broad-except
            LOGGER.error("Failed to precache media for %s: %s", self, ex)


class GameMetadata(models.Model):
    """Additional key-value metadata attached to a game"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    key = models.CharField(max_length=16)
    value = models.CharField(max_length=255)


class GameAlias(models.Model):
    """Alternate names and spellings a game might be known as"""
    game = models.ForeignKey(Game, related_name="aliases", on_delete=models.CASCADE)
    slug = models.SlugField()
    name = models.CharField(max_length=255)


class ScreenshotManager(models.Manager):
    """Model manager for game screenshots"""

    def published(self, user=None, is_staff=False):
        """Return only published screenshots for regular users"""
        query = self.get_queryset()
        query = query.order_by("uploaded_at")
        if is_staff:
            return query
        if user:
            return query.filter(Q(published=True) | Q(uploaded_by=user))
        return query.filter(published=True)


class Screenshot(models.Model):
    """Screenshots for games"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="games/screenshots")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.CharField(max_length=256, null=True, blank=True)
    published = models.BooleanField(default=False)

    objects = ScreenshotManager()

    def __str__(self):
        desc = self.description if self.description else self.game.name
        return "%s: %s (uploaded by %s)" % (self.game, desc, self.uploaded_by)


class InstallerManager(models.Manager):
    """Model manager for Installer"""

    def published(self):
        """Return published installers"""
        return self.get_queryset().filter(published=True)

    def unpublished(self):
        """Return unpublished installers"""
        return self.get_queryset().filter(published=False)

    def drafts(self):
        """Return unpublished installers"""
        return self.get_queryset().filter(published=False, draft=True)

    def new(self):
        """Return new installers that don't have any edits"""
        return [
            installer
            for installer in self.get_queryset().filter(
                published=False,
                draft=False
            ).order_by("-updated_at")
            if not Version.objects.filter(
                object_id=installer.id, content_type__model="installer"
            ).count()
        ]

    def abandoned(self):
        """Return the installer with 'Change Me' version that haven't received any modifications"""
        return [
            installer
            for installer in self.get_queryset().filter(version="Change Me")
            if not Version.objects.filter(
                object_id=installer.id, content_type__model="installer"
            ).count()
        ]

    def _fuzzy_search(self, slug, return_models=False):
        try:
            # Try returning installers by installer slug
            installer = self.get_queryset().get(slug=slug)
            return [installer]
        except ObjectDoesNotExist:

            # Try getting installers by game name
            try:
                game = Game.objects.get(slug=slug)
            except ObjectDoesNotExist:
                game = None

            if not game:
                try:
                    game = Game.objects.get(aliases__slug=slug)
                except ObjectDoesNotExist:
                    game = None
            if game:
                installers = self.get_queryset().filter(game=game, published=True)

                auto_installers = []
                for platform in game.platforms.exclude(default_installer__isnull=True):
                    auto_installers.append(AutoInstaller(game, platform))

                if installers or auto_installers:
                    return list(chain(installers, auto_installers))

            # Try auto installers
            for platform in Platform.objects.exclude(default_installer__isnull=True):
                suffix = "-" + platform.slug
                if slug.endswith(suffix):
                    game_slug = slug[: -len(suffix)]
                    try:
                        games = [Game.objects.get(slug=game_slug)]
                    except Game.DoesNotExist:
                        games = Game.objects.filter(slug__startswith=game_slug)

                    for game in games:
                        auto_installer = self.get_auto_installer(
                            slug, game, platform, return_models=return_models
                        )
                        if auto_installer:
                            return auto_installer

            # A bit hackish, return_models is used for filter and not with get
            if return_models:
                return self.none()
            raise

    @staticmethod
    def get_auto_installer(slug, game, platform, return_models=False):
        """Doesn't make a lot of sense, this is game specific and
        should probably not be here.
        """
        if return_models:
            try:
                auto_installer = AutoInstaller(game, platform)
                if auto_installer.slug == slug:
                    return [auto_installer]
            except ObjectDoesNotExist:
                pass
        else:
            auto_installers = game.get_default_installers()
            for auto_installer in auto_installers:
                if auto_installer["slug"] == slug:
                    return [auto_installer]

    def fuzzy_get(self, slug):
        """Return either the installer that matches exactly 'slug' or the
        installers with game matching slug.
        Installers are always returned in a list.
        TODO: Deprecate in favor of fuzzy_filter
        """
        return self._fuzzy_search(slug)

    def fuzzy_filter(self, slug):
        """Like fuzzy_get but always returns a list of model instances"""
        return self._fuzzy_search(slug, return_models=True)

    def get_json(self, slug):
        """Return the installer identified by its slug as a JSON document"""
        try:
            installers = self.fuzzy_get(slug)
        except ObjectDoesNotExist:
            installer_data = []
        else:
            if installers and isinstance(installers[0], dict):
                installer_data = installers
            else:
                installer_data = [installer.as_dict() for installer in installers]
        try:
            game = Game.objects.get(slug=slug)
            installer_data += game.get_default_installers()
        except ObjectDoesNotExist:
            pass
        if not installer_data:
            raise Installer.DoesNotExist
        return json.dumps(installer_data, indent=2)


class BaseInstaller(models.Model):
    """Base class for Installer-like classes."""

    class Meta:
        """Model configuration"""
        abstract = True

    @property
    def raw_script(self):
        """Return the installer script without its metadata"""
        return self.as_dict(with_metadata=False)

    @property
    def game_slug(self):
        """Return the game slug, a bit useless... Maybe for a serializer?"""
        return self.game.slug

    def as_dict(self, with_metadata=True):
        """Return the installer data as a dict"""
        try:
            yaml_content = load_yaml(self.content) or {}
        except (yaml.parser.ParserError, yaml.scanner.ScannerError):
            LOGGER.error("Installer with invalid YAML. Deleting immediatly.")
            if self.id:
                self.delete()
            return {}

        # Allow pasting raw install scripts (which are served as lists)
        if isinstance(yaml_content, list):
            yaml_content = yaml_content[0]

        # If yaml content evaluates to a string return an empty dict
        if isinstance(yaml_content, six.string_types):
            return {}

        # Do not add metadata if the clean argument has been passed
        if with_metadata:
            yaml_content["game_slug"] = self.game.slug
            yaml_content["version"] = self.version
            yaml_content["description"] = self.description
            yaml_content["notes"] = self.notes
            yaml_content["name"] = self.game.name
            yaml_content["year"] = self.game.year
            yaml_content["steamid"] = self.game.steamid
            yaml_content["gogslug"] = self.game.gogslug
            yaml_content["humblestoreid"] = self.game.humblestoreid
            try:
                yaml_content["runner"] = self.runner.slug
            except ObjectDoesNotExist:
                yaml_content["runner"] = ""
            # Set slug to both slug and installer_slug for backward compatibility
            # reasons with the client. Remove installer_slug sometime in the future
            yaml_content["slug"] = self.slug
            yaml_content["installer_slug"] = self.slug
        return yaml_content

    def as_yaml(self):
        """Return the installer as a YAML document"""
        return dump_yaml(self.as_dict())

    def as_json(self):
        """Return the installer as a JSON document"""
        return json.dumps(self.as_dict(), indent=2)

    def as_cleaned_yaml(self):
        """Return the YAML installer without the metadata"""
        return dump_yaml(self.as_dict(with_metadata=False))

    def as_cleaned_json(self):
        """Return the JSON installer without the metadata"""
        return json.dumps(self.as_dict(with_metadata=False), indent=2)

    def build_slug(self, version):
        """Generate a slug that will prevent clashes with other installers"""
        slug = "%s-%s" % (slugify(self.game.name)[:29], slugify(version)[:20])
        return get_auto_increment_slug(self.__class__, self, slug)


@reversion.register()
class Installer(BaseInstaller):
    """Game installer model"""

    RATINGS = {
        "5": "Platinum: installs and runs flawlessly",
        "4": "Gold: works flawlessly with some minor tweaking",
        "3": (
            'Silver: works excellently for "normal" use but some '
            "features may be broken"
        ),
        "2": "Bronze: works: but has some issues: even for normal use",
        "1": "Garbage: game is not playable",
    }

    game = models.ForeignKey(Game, related_name="installers", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    runner = models.ForeignKey("runners.Runner", on_delete=models.CASCADE)

    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=32)
    description = models.CharField(max_length=512, blank=True, null=True)
    notes = models.TextField(blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="moderator",
        blank=True,
        null=True,
    )
    draft = models.BooleanField(default=True)
    rating = models.CharField(max_length=24, choices=RATINGS.items(), blank=True)
    protected = models.BooleanField(default=False)

    # Relevant for edit submissions only: Reason why the proposed change
    # is necessecary or useful
    reason = models.CharField(max_length=512, blank=True, null=True)

    # Collection manager
    objects = InstallerManager()

    class Meta:
        """Model configuration"""
        ordering = ("-rating", "version")

    def __str__(self):
        return self.slug

    def set_default_installer(self):
        """Creates the default content for installer when they are first created.

        This method should load from installer templates once they are implemented.
        """
        if self.game and self.game.steam_support():
            installer_data = {"game": {"appid": self.game.steamid}}
            self.version = "Steam"
        else:
            installer_data = DEFAULT_INSTALLER
        self.content = dump_yaml(installer_data)

    @property
    def revisions(self):
        """Return the revisions for this installer"""
        return [
            InstallerRevision(version)
            for version in Version.objects.filter(
                content_type__model="installer", object_id=self.id
            )
        ]

    @property
    def latest_version(self):
        """Return the latest version for this installer"""
        versions = Version.objects.filter(
            content_type__model="installer",
            object_id=self.id
        ).order_by("-revision__date_created")
        for version in versions:
            if not version.field_dict["draft"]:
                return version

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.slug = self.build_slug(self.version)
        return super(Installer, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class InstallerHistory(BaseInstaller):
    """Past versions of installers

    Yes, that's what django-reversion is supposed to be for but we used it in a backwards way,
    to store submissions instead of past revisions.

    This is a simplified version of the model anyway since we don't have to keep track  of the
    published aspect of it.
    """
    installer = models.ForeignKey(Installer, related_name="past_versions", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    runner = models.ForeignKey("runners.Runner", on_delete=models.CASCADE)
    version = models.CharField(max_length=32)
    description = models.CharField(max_length=512, blank=True, null=True)
    notes = models.TextField(blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    @classmethod
    def create_from_installer(cls, installer):
        """Create a copy of the installer"""
        return cls.objects.create(
            installer=installer,
            user=installer.user,
            runner=installer.runner,
            version=installer.version,
            description=installer.description,
            notes=installer.notes,
            content=installer.content
        )

    def __str__(self):
        return "Snapshot of installer %s at %s" % (self.installer, self.created_at)


class BaseIssue(models.Model):
    """Abstract class for issue-like models"""
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    submitted_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    class Meta:
        """This is an abstract model"""
        abstract = True

    def __str__(self):
        return "[{user} {date}] {summary}".format(
            date=self.submitted_on.date(),
            user=self.submitted_by,
            summary=self.description[:24],
        )


class InstallerIssue(BaseIssue):
    """Model to store problems about installers or update requests"""

    installer = models.ForeignKey(
        Installer, related_name="issues", on_delete=models.CASCADE
    )
    solved = models.BooleanField(default=False)

    def get_absolute_url(self):
        """Return url for admin form"""
        return reverse("admin:games_installerissue_change", args=(self.id,))


class InstallerIssueReply(BaseIssue):
    """Reply to an issue"""

    issue = models.ForeignKey(
        InstallerIssue, related_name="replies", on_delete=models.CASCADE
    )


class GameLibrary(models.Model):
    """Model to store user libraries"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    games = models.ManyToManyField(Game, related_name="libraries")

    class Meta:
        """Model configuration"""
        verbose_name_plural = "game libraries"

    def __str__(self):
        return "%s's library" % self.user.username


class GameSubmission(models.Model):
    """User submitted game"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="submissions",
        on_delete=models.CASCADE
    )
    game = models.ForeignKey(
        Game,
        related_name="submissions",
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True)
    reason = models.TextField(blank=True, null=True)

    class Meta:
        """Model configuration"""
        verbose_name = "User submitted game"

    @property
    def status(self):
        """status string for the submission"""
        return "accepted" if self.accepted_at else "pending"

    def __str__(self):
        return "{0} submitted {1} on {2}".format(self.user, self.game, self.created_at)

    def accept(self):
        """Accept the submission and notify the author"""
        if self.accepted_at:
            LOGGER.warning("Submission already accepted")
            return
        self.game.is_public = True
        self.game.save()
        self.accepted_at = datetime.datetime.now()
        self.save()
        messages.send_game_accepted(self.user, self.game)


class GameLink(models.Model):
    """Web links associated to a game"""
    WEBSITE_CHOICES = (
        ('battlenet', 'Battle.net'),
        ('github', 'Github'),
        ('isthereanydeal', 'IsThereAnyDeal'),
        ('lemonamiga', 'Lemon Amiga'),
        ('mobygames', 'MobyGames'),
        ('origin', 'Origin'),
        ('pcgamingwiki', 'PCGamingWiki'),
        ('ubisoft', 'Ubisoft'),
        ('wikipedia', 'Wikipedia'),
        ('winehq', 'WineHQ AppDB'),
    )
    game = models.ForeignKey(Game, related_name="links", on_delete=models.CASCADE)
    website = models.CharField(blank=True, choices=WEBSITE_CHOICES, max_length=32)
    url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Additional configuration for model"""

        verbose_name = "External link"
        ordering = ["website"]


class InstallerRevision(BaseInstaller):  # pylint: disable=too-many-instance-attributes
    """Revision for an installer"""
    def __init__(self, version):
        super(InstallerRevision, self).__init__()
        self._version = version
        self.id = version.pk  # pylint: disable=C0103
        installer_data = self.get_installer_data()
        self.game = Game.objects.get(pk=installer_data["game"])

        self.name = self.game.name

        try:
            self.comment = self._version.revision.comment
            self.user = self._version.revision.user
            self.created_at = self._version.revision.date_created
        except Revision.DoesNotExist:
            LOGGER.warning("No revision found for %s", self._version)
            self.comment = ""
            self.user = None
            self.created_at = None
        self.draft = installer_data["draft"]
        self.published = installer_data["published"]
        self.rating = installer_data["rating"]

        self.script = installer_data["script"]
        self.content = installer_data["content"]

        self.user = self.user
        try:
            self.runner = Runner.objects.get(pk=installer_data["runner"])
        except Runner.DoesNotExist:
            self.runner = None
        self.slug = installer_data["slug"]
        self.version = installer_data["version"]
        self.description = installer_data["description"]
        self.notes = installer_data["notes"]
        self.reason = installer_data["reason"]

        self.installer_id = self._version.object_id

    def __str__(self):
        return self.comment

    @classmethod
    def iterate_versions(cls, version_type="submission"):
        """List all versions of a given type"""
        return Version.objects.filter(
            content_type__model="installer",
            revision__comment__startswith=f"[{version_type}]"
        )

    @classmethod
    def remove_dupe_submissions(cls):
        """Ensure installers only have 1 submission"""
        revisions = [cls(version) for version in cls.iterate_versions()]
        dupe_submissions = []
        for revision in revisions:
            try:
                installer = Installer.objects.get(id=revision.installer_id)
            except Installer.DoesNotExist:
                LOGGER.info("No installer with ID %s", revision.installer_id)
                revision.delete()
                continue

            num_sub = 0
            for rev in installer.revisions:
                if rev.comment.startswith("[submission]"):
                    num_sub += 1
            if num_sub > 1:
                if installer not in dupe_submissions:
                    dupe_submissions.append(installer)
        for dupe in dupe_submissions:
            print("Duplicate sub for ", dupe)
        print(f"{len(dupe_submissions)} installers to clean")
        for installer in dupe_submissions:
            revisions = sorted(
                [r for r in installer.revisions if r.comment.startswith("[submission]")],
                key=lambda x: x.revision.date_created,
                reverse=True
            )
            for rev in revisions[1:]:
                rev.set_to_draft()

    def set_to_draft(self):
        """Change the submission back to draft"""
        self.comment = self.comment.replace("[submission]", "[draft]")
        self._version.revision.comment = self.comment
        self._version.revision.save()

    @property
    def revision(self):
        """Accessor for the revision"""
        if self._version.revision:
            return self._version.revision

    @property
    def revision_id(self):
        """Accessor for the revision id if there is one"""
        if self._version.revision:
            return self._version.revision.id

    def get_installer_data(self):
        """Return the data saved in the revision in an usable format"""
        installer_data = json.loads(self._version.serialized_data)[0]["fields"]
        installer_data["script"] = load_yaml(installer_data["content"])
        installer_data["id"] = self.id
        # Return a defaultdict to prevent key errors for new fields that
        # weren't present in previous revisions
        default_installer_data = defaultdict(str)
        default_installer_data.update(installer_data)
        return default_installer_data

    def _clear_old_revisions(self, original_revision=None, author=None, date=None):
        """Delete revisions older than a given date and from a given author"""
        try:
            installer = Installer.objects.get(pk=self.installer_id)
        except Installer.DoesNotExist:
            # Revision is for a deleted installer
            original_revision.delete()
            return
        if not author:
            if not original_revision:
                LOGGER.warning("Missing original revision, skipping the rest.")
                return
            author = original_revision.user
            date = original_revision.date_created

        # Clean earlier drafts from the same submitter
        for revision in installer.revisions:
            if author and date and any([
                revision.user != author,
                revision.created_at > date
            ]):
                continue
            revision._version.revision.delete()  # pylint: disable=protected-access

    def delete(self, using=None, keep_parents=False):  # pylint: disable=unused-argument
        """Delete the revision and the previous ones from the same author"""
        self._clear_old_revisions(original_revision=self._version.revision)

    def accept(self, moderator=None, installer_data=None):
        """Accepts an installer submission

        Also clears any earlier draft created by the same user.
        The data submitted by the user can be overridden by a moderator in the
        installer_data dict.
        """

        submission_author = self._version.revision.user
        submission_date = self._version.revision.date_created
        # Since the reversion package is used in a backwards way,
        # the installer is "reverted" to its future state (versions are
        # supposed to store past states of objects but they are used for
        # storing potential future versions in our case).
        self._version.revert()

        installer = Installer.objects.get(pk=self.installer_id)
        installer.published = True
        installer.draft = False

        # Keep a snapshot of the current installer (if a moderator is involved, otherwise is this
        # accepted automatically by a script and doesn't need a revision)
        if moderator:
            InstallerHistory.create_from_installer(installer)
            installer.published_by = moderator

        if installer_data:
            # Only fields editable in the dashboard will be affected
            # FIXME also persist runner
            installer.version = installer_data["version"]
            installer.notes = installer_data["notes"]
            installer.description = installer_data["description"]
            installer.content = installer_data["content"]
        installer.save()

        self._clear_old_revisions(author=submission_author, date=submission_date)


class AutoInstaller(BaseInstaller):  # pylint: disable=too-many-instance-attributes
    """Auto-generated installer"""
    published = True
    draft = False
    auto = True
    description = ""
    notes = ""
    user = None
    rating = None
    created_at = None
    updated_at = None

    def __init__(self, game, platform):
        super(AutoInstaller, self).__init__()
        self.game = game
        if platform not in game.platforms.all():
            raise ObjectDoesNotExist
        self.script = platform.default_installer
        self.content = json.dumps(self.script)
        self.name = game.name
        self.version = platform.name
        self.slug = "-".join((game.slug[:30], platform.slug[:20]))
        self.platform = platform.slug
        self.runner = Runner.objects.get(slug=self.script.pop("runner"))

    @property
    def raw_script(self):
        return self.script
