"""Models for main lutris app"""

# pylint: disable=no-member,too-few-public-methods,too-many-lines
import os
import shutil
import datetime
import json
import logging
import random
import re
from itertools import chain

import six
import yaml
from bitfield import BitField
from sorl.thumbnail import get_thumbnail
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import models, IntegrityError
from django.db.models import Count, Q
from django.db.models.query import QuerySet
from django.urls import reverse

from common.util import get_auto_increment_slug, slugify, load_yaml, dump_yaml
from emails import messages
from emails.messages import notify_rejected_installer
from games.util import steam, gog
from platforms.models import Platform
from runners.models import Runner
from providers.models import ProviderGame


LOGGER = logging.getLogger(__name__)
DEFAULT_INSTALLER = {
    "files": [{"file_id": "http://location"}, {"unredistribuable_file": "N/A"}],
    "installer": [{"move": {"src": "file_id", "dst": "$GAMEDIR"}}],
}


def clean_string(string):
    return string.replace("\r\n", "\n").strip()


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
        return reverse("games_by_company", kwargs={"company": self.pk})

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


class Genre(models.Model):
    """Gaming genre"""

    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

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
                | Q(provider_games__provider__name__in=("gog", "steam", "humble"))
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
        ("kernel_ac", "Infected with kernel level anticheat"),
        ("adult_only", "Adult only"),
    )

    # These model fields are editable by the user
    TRACKED_FIELDS = [
        "name",
        "year",
        "platforms",
        "genres",
        "publisher",
        "developer",
        "website",
        "description",
        "title_logo",
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
    coverart = models.ImageField(upload_to="igdb", blank=True)
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
    provider_games = models.ManyToManyField(
        ProviderGame, related_name="games", blank=True
    )

    # Indicates whether this data row is a changeset for another data row.
    # If so, this attribute is not NULL and the value is the ID of the
    # corresponding data row
    change_for = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE
    )

    # Adding Discord App ID for Rich Presence Client
    discord_id = models.CharField(
        max_length=18,
        default="",
        null=True,
        blank=True,
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
        _slugs = self.provider_games.filter(provider__name="humblebundle").values_list(
            "slug", flat=True
        )
        if _slugs:
            return _slugs[0]
        return ""

    @property
    def user_count(self):
        """How many users have the game in their libraries"""
        return self.librarygame_set.count()

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
            if self.change_for:
                slug = self.change_for.slug
            else:
                slug = self.slug
            return settings.ROOT_URL + reverse("get_banner", kwargs={"slug": slug})
        return ""

    @property
    def icon_url(self):
        """Return URL for the game icon"""
        if self.icon:
            if self.change_for:
                slug = self.change_for.slug
            else:
                slug = self.slug
            return settings.ROOT_URL + reverse("get_icon", kwargs={"slug": slug})
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

    def get_provider_links(self):
        """Return a dict of links created from provider games data"""
        provider_games = {p.provider.name: p for p in self.provider_games.all()}
        links = {}
        if "igdb" in provider_games:
            url = provider_games["igdb"].metadata.get("url")
            if url:
                links["igdb"] = url
        if "steam" in provider_games:
            appid = provider_games["steam"].slug
            links["steam"] = f"https://store.steampowered.com/app/{appid}"
            links["protondb"] = f"https://www.protondb.com/app/{appid}"
            links["steamdb"] = f"https://steamdb.info/app/{appid}"
            links["isthereanydeal"] = f"https://isthereanydeal.com/steam/app/{appid}"
        if "mame" in provider_games:
            romname = provider_games["mame"].slug
            links["gamesdatabase"] = f"https://www.gamesdatabase.org/mame-rom/{romname}"
            links["arcadedatabase"] = (
                f"http://adb.arcadeitalia.net/dettaglio_mame.php?game_name={romname}"
            )
        return links

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
            if entry in ["platforms", "genres"]:  # convert M2M relations to string
                old_value = ", ".join(
                    "[{0}]".format(str(x)) for x in list(old_value.all())
                )
                new_value = ", ".join(
                    "[{0}]".format(str(x)) for x in list(new_value.all())
                )
            if entry == "description":
                old_comparator = clean_string(old_value)
                new_comparator = clean_string(new_value)
            else:
                old_comparator = old_value
                new_comparator = new_value

            if old_comparator != new_comparator:
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
        GameAlias.objects.create(game=self, name=other_game.name, slug=other_game.slug)

        # Merge genres
        for genre in other_game.genres.all():
            self.genres.add(genre)

        # Merge platforms
        for platform in other_game.platforms.all():
            self.platforms.add(platform)

        # Move user libraries
        LibraryGame.objects.filter(game=other_game).update(game=self)

        # Move provider games
        for provider_game in other_game.provider_games.all():
            try:
                self.provider_games.add(provider_game)
            except IntegrityError:
                # This provider game already exist on this game
                pass

        # Merge Steam ID if none is present
        if not self.steamid:
            self.steamid = other_game.steamid

        # Merge year if none is provided
        if not self.year:
            self.year = other_game.year

        # Merge icon if none exist
        if not self.icon.name:
            self.icon = other_game.icon

        # Merge banner if there is none
        if not self.title_logo.name:
            self.title_logo = other_game.title_logo

        # Merge cover if there is none
        if not self.coverart.name:
            self.coverart = other_game.coverart

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

        self.save()
        other_game.delete()

    def has_installer(self):
        """Return whether this game has an installer"""
        return self.installers.exists() or self.has_auto_installers()

    def has_auto_installers(self):
        """Return whether this game has auto-generated installers"""
        platform_has_autoinstaller = self.platforms.filter(
            default_installer__isnull=False
        ).exists()
        if platform_has_autoinstaller:
            return True
        return self.provider_games.filter(
            Q(provider__name="gog")
            | Q(provider__name="steam")
            | Q(provider__name="humblebundle")
        ).exists()

    def get_absolute_url(self):
        """Return the absolute url for a game"""
        if self.change_for:
            slug = self.change_for.slug
        else:
            slug = self.slug
        return reverse("game_detail", kwargs={"slug": slug})

    def precache_media(self, force=False):
        """Prerenders thumbnails so we can host them as static files"""
        icon_path = os.path.join(settings.MEDIA_ROOT, self.icon.name)
        if self.icon.name and os.path.exists(icon_path):
            self.precache_icon(force)
        banner_path = os.path.join(settings.MEDIA_ROOT, self.title_logo.name)
        if self.title_logo.name and os.path.exists(banner_path):
            self.precache_banner(force)

    def precache_icon(self, force=False):
        """Render the icon and place it in the icons folder"""
        dest_file = os.path.join(self.ICON_PATH, "%s.png" % self.slug)
        if os.path.exists(dest_file):
            if force:
                os.unlink(dest_file)
            else:
                return
        try:
            thumbnail = get_thumbnail(
                self.icon, settings.ICON_SIZE, crop="center", format="PNG"
            )
        except AttributeError as ex:
            LOGGER.error("Icon failed for %s: %s", self, ex)
            return
        shutil.copy(os.path.join(settings.MEDIA_ROOT, thumbnail.name), dest_file)

    def precache_banner(self, force=False):
        """Render the icon and place it in the banners folder"""
        dest_file = os.path.join(self.BANNER_PATH, "%s.jpg" % self.slug)
        if os.path.exists(dest_file):
            if force:
                os.unlink(dest_file)
            else:
                return
        try:
            thumbnail = get_thumbnail(
                self.title_logo, settings.BANNER_SIZE, crop="center"
            )
        except AttributeError as ex:
            LOGGER.error(
                "Could not write banner to %s from %s for %s: %s",
                dest_file,
                self.title_logo,
                self,
                ex,
            )
            return
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
        self.title_logo = ContentFile(gog.get_logo(gog_game), "gog-%s.jpg" % self.gogid)

    def steam_support(self):
        """Return the platform supported by Steam"""
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
        provider_with_autoinstallers = ["gog", "steam", "humblebundle"]
        provider_names = {
            "gog": "GOG",
            "steam": "Steam",
            "humblebundle": "Humble Bundle",
        }
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
        for provider_game in self.provider_games.filter(
            provider__name__in=provider_with_autoinstallers
        ):
            installer = {
                "name": self.name,
                "game_slug": self.slug,
                "runner": "auto",
                "version": provider_names[provider_game.provider.name] + "(Auto)",
                "slug": "%s:%s"
                % (provider_game.provider.name, provider_game.internal_id),
                "description": (
                    "Make sure you have connected your %s account in Lutris and that you own this game."
                    % provider_names[provider_game.provider.name]
                ),
                "published": True,
                "auto": True,
            }
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
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class GameAlias(models.Model):
    """Alternate names and spellings a game might be known as"""

    game = models.ForeignKey(Game, related_name="aliases", on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255)
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

    def unpublished(self):
        """Return unpublished screenshots"""
        return (
            self.get_queryset()
            .prefetch_related("game", "uploaded_by")
            .order_by("uploaded_at")
            .filter(published=False)
        )


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


class InstallerHistoryManager(models.Manager):
    """Model manager for InstallerHistory"""

    def get_filtered(self, filter: dict) -> QuerySet:
        """Return history of installers filtered by params
        filter:
            created_from (timestamp): history period start
            created_to (timestamp): history period end
        """
        filter_ = {}
        if "created_from" in filter:
            filter_["created_at__gte"] = filter["created_from"]
        if "created_to" in filter:
            filter_["created_at__lt"] = filter["created_to"]
        return self.get_queryset().filter(**filter_)


class InstallerManager(models.Manager):
    """Model manager for Installer"""

    def get_filtered(self, filter: dict) -> QuerySet:
        """Return installers filtered by params
        filter:
            published (boolean): is published
            draft (boolean): is draft
            created_from (timestamp): installer creation period start
            created_to (timestamp): installer creation period end
            updated_from (timestamp): installer modification period start
            updated_to (timestamp): installer modification period end
        """
        filter_ = {}
        for f in {"published", "draft"}:
            if f in filter:
                filter_[f] = filter[f]
        if "created_from" in filter:
            filter_["created_at__gte"] = filter["created_from"]
        if "created_to" in filter:
            filter_["created_at__lt"] = filter["created_to"]
        if "updated_from" in filter:
            filter_["updated_at__gte"] = filter["updated_from"]
        if "updated_to" in filter:
            filter_["updated_at__lt"] = filter["updated_to"]
        return self.get_queryset().filter(**filter_)

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
                        if len(slug) > 40:
                            games = Game.objects.filter(slug__startswith=game_slug)
                        else:
                            games = []

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
        yaml_content = {}
        try:
            script_content = load_yaml(self.content) or {}
        except (yaml.parser.ParserError, yaml.scanner.ScannerError) as ex:
            if self.id:
                LOGGER.error(
                    "Installer for %s %s contains errors (%s). Deleting immediatly.",
                    self.game,
                    self,
                    ex,
                )
                self.delete()
            else:
                LOGGER.error(
                    "Non finalized script %s %s contains errors: %s",
                    self.game,
                    self,
                    ex,
                )
            return {}

        # Allow pasting raw install scripts (which are served as lists)
        if isinstance(yaml_content, list):
            yaml_content = yaml_content[0]

        # If yaml content evaluates to a string return an empty dict
        if isinstance(yaml_content, six.string_types):
            return {}

        # Do not add metadata if the clean argument has been passed
        if not with_metadata:
            return script_content

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
        yaml_content["script"] = script_content
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


class Installer(BaseInstaller):
    """Game installer model"""

    game = models.ForeignKey(Game, related_name="installers", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    runner = models.ForeignKey("runners.Runner", on_delete=models.CASCADE)

    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=32)
    description = models.CharField(max_length=512, blank=True, null=True)
    notes = models.TextField(blank=True)
    credits = models.TextField(blank=True)
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
    maintainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="maintainer",
        blank=True,
        null=True,
    )
    draft = models.BooleanField(default=False)
    rating = models.CharField(max_length=24, choices=(("0", "Do not use"),), blank=True)

    # Relevant for edit submissions only: Reason why the proposed change
    # is necessecary or useful
    reason = models.CharField(max_length=512, blank=True, null=True)
    review = models.CharField(max_length=512, blank=True, null=True)

    # Wine pinning management. Pinning Wine versions is heavily discouraged,
    # installers having a pinned Wine version without a justification will
    # show a warning to the user.
    pinned = models.BooleanField(default=False)
    pin_reason = models.URLField(blank=True)

    # Some installer can be flagged as dangerous.
    flagged = models.BooleanField(default=False)

    # Collection manager
    objects = InstallerManager()

    class Meta:
        """Model configuration"""

        ordering = ("version",)

    def __str__(self):
        return self.slug

    def is_playable(self):
        """Return value of rating if the installer has a verified one"""
        rating = self.ratings.filter(verified=True).first()
        if rating:
            return rating.playable
        return None

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
    def edit_url(self):
        """Return absolute URL to the edit installer form"""
        return settings.ROOT_URL + reverse("edit_installer", kwargs={"slug": self.slug})

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
    This is a simplified version of the model
    """

    installer = models.ForeignKey(
        Installer, related_name="past_versions", on_delete=models.CASCADE
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    runner = models.ForeignKey("runners.Runner", on_delete=models.CASCADE)
    version = models.CharField(max_length=32)
    description = models.CharField(max_length=512, blank=True, null=True)
    notes = models.TextField(blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    # Collection manager
    objects = InstallerHistoryManager()

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
            content=installer.content,
        )

    def __str__(self):
        return "Snapshot of installer %s at %s" % (self.installer, self.created_at)


class InstallerDraft(BaseInstaller):
    """Model for user drafts"""

    game = models.ForeignKey(
        Game, related_name="draft_installers", on_delete=models.CASCADE
    )
    base_installer = models.ForeignKey(
        Installer, related_name="drafts", on_delete=models.CASCADE, null=True
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    runner = models.ForeignKey("runners.Runner", on_delete=models.CASCADE, null=True)
    version = models.CharField(max_length=32)
    description = models.CharField(max_length=512, blank=True, null=True)
    notes = models.TextField(blank=True)
    credits = models.TextField(blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(null=True)
    draft = models.BooleanField(default=True)
    # Relevant for edit submissions only: Reason why the proposed change
    # is necessecary or useful
    reason = models.CharField(max_length=512, blank=True, null=True)
    review = models.CharField(max_length=512, blank=True, null=True)

    def __str__(self):
        return self.version

    @property
    def slug(self):
        """Autogenerated slug for drafts"""
        return "%s-draft-%s" % (slugify(self.game.name)[:29], self.id)

    def reject(self, installer_data):
        """Reject the submission, setting it back to draft."""
        self.review = installer_data["review"]
        self.draft = True
        self.save()
        if self.review:
            notify_rejected_installer(self, self.review, self.user)

    def accept(self, moderator=None, installer_data=None):
        """Accepts an installer submission
        The data submitted by the user can be overridden by a moderator in the
        installer_data dict.
        """
        if self.base_installer:
            installer = self.base_installer
            # Keep a snapshot of the current installer (if a moderator is involved, otherwise is this
            # accepted automatically by a script and doesn't need a revision)
            if moderator:
                InstallerHistory.create_from_installer(installer)
                installer.published_by = moderator
        else:
            installer = Installer()
            installer.user = self.user
            installer.game = self.game
        installer.runner = self.runner
        installer.description = self.description
        installer.content = self.content
        installer.credits = self.credits
        installer.version = self.version
        installer.notes = self.notes
        installer.published = True
        installer.draft = False
        if installer_data:
            # Only fields editable in the dashboard will be affected
            # FIXME also persist runner
            installer.version = installer_data["version"]
            installer.notes = installer_data["notes"]
            installer.description = installer_data["description"]
            installer.content = installer_data["content"]
        installer.save()
        self.delete()


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

    class Meta:
        """Model configuration"""

        verbose_name_plural = "game libraries"

    def __str__(self):
        return "%s's library" % self.user.username


class LibraryCategory(models.Model):
    """Model to represent a user defined category"""

    gamelibrary = models.ForeignKey(
        GameLibrary, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=256)


class LibraryGame(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=256, null=True)
    slug = models.CharField(max_length=256, null=True)
    gamelibrary = models.ForeignKey(
        GameLibrary, on_delete=models.CASCADE, related_name="games"
    )
    playtime = models.FloatField(default=0, null=True)
    runner = models.CharField(max_length=64, null=True)
    platform = models.CharField(max_length=255, null=True)
    service = models.CharField(max_length=64, null=True)
    service_id = models.CharField(max_length=255, null=True)
    lastplayed = models.IntegerField(null=True, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField(LibraryCategory, blank=True)

    def __str__(self):
        return f"{self.name} ({self.playtime}, {self.lastplayed})"

    def get_slug(self):
        """Temporary only"""
        if self.slug:
            return self.slug
        if self.game:
            return self.game.slug

    def get_name(self):
        """Temporary"""
        if self.name:
            return self.name
        if self.game:
            return self.game.name

    def get_category_names(self):
        return [c.name for c in self.categories.all()]

    @property
    def coverart(self):
        if self.game and self.game.coverart:
            return self.game.coverart.url

    @property
    def banner(self):
        if self.game:
            return self.game.banner_url

    @property
    def icon(self):
        if self.game:
            return self.game.icon_url

    class Meta:
        """Model configuration"""

        ordering = ("slug",)


class StoreLibrary(models.Model):
    """Model to keep track of a user's library for a given store"""

    store_name = models.CharField(max_length=64)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class GameSubmission(models.Model):
    """User submitted game"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="submissions", on_delete=models.CASCADE
    )
    game = models.ForeignKey(Game, related_name="submissions", on_delete=models.CASCADE)
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
        """Accept the game submission and notify the author"""
        if self.accepted_at:
            LOGGER.warning("Game submission already accepted")
            return
        self.game.is_public = True
        self.game.save()
        self.accepted_at = datetime.datetime.now()
        self.save()
        messages.send_game_accepted(self.user, self.game)


class GameLink(models.Model):
    """Web links associated to a game"""

    WEBSITE_CHOICES = (
        ("battlenet", "Battle.net"),
        ("github", "Github"),
        ("isthereanydeal", "IsThereAnyDeal"),
        ("lemonamiga", "Lemon Amiga"),
        ("mobygames", "MobyGames"),
        ("origin", "Origin"),
        ("pcgamingwiki", "PCGamingWiki"),
        ("ubisoft", "Ubisoft"),
        ("wikipedia", "Wikipedia"),
        ("winehq", "WineHQ AppDB"),
    )
    game = models.ForeignKey(Game, related_name="links", on_delete=models.CASCADE)
    website = models.CharField(blank=True, choices=WEBSITE_CHOICES, max_length=32)
    url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Additional configuration for model"""

        verbose_name = "External link"
        ordering = ["website"]


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


class Rating(models.Model):
    """Model to store installer ratings"""

    installer = models.ForeignKey(
        Installer, on_delete=models.CASCADE, related_name="ratings"
    )
    playable = models.BooleanField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return "%s: %s" % (
            "PLAYABLE" if self.playable else "NON PLAYABLE",
            self.installer.slug,
        )


class Quirk(models.Model):
    """Model to store quirks and caveats for ratings"""

    rating = models.ForeignKey(Rating, on_delete=models.CASCADE, related_name="quirks")
    value = models.CharField(max_length=256)


class ShaderCache(models.Model):
    """Model to reference shader cache locations"""

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="shaders")
    updated_at = models.DateTimeField(auto_now=True)
    url = models.CharField(max_length=256)
