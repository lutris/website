"""DRF serializers for Game models"""
# pylint: disable=too-few-public-methods
import logging

from rest_framework import serializers

from games import models
from platforms.models import Platform
from providers.serializers import ProviderGameSerializer
from accounts.serializers import UserSerializer

LOGGER = logging.getLogger(__name__)


class PlatformSerializer(serializers.ModelSerializer):
    """Serializer for Platforms"""
    class Meta:
        """Model and field definitions"""
        model = Platform
        fields = ('name',)


class GenreSerializer(serializers.ModelSerializer):
    """Serializer for Genres"""

    class Meta:
        """Model and field definitions"""
        model = models.Genre
        fields = ('name',)



class GameAliasSerializer(serializers.ModelSerializer):
    """Serializer for game aliases, used to provide an alias list to GameSerializer"""
    class Meta:
        """Model and field definitions"""
        model = models.GameAlias
        fields = ('slug', 'name')

class MicroGameSerializer(serializers.ModelSerializer):
    """Another Serializer for Games since DRF doesn't support recursive relationships.
    Also can be used for very small reference to games"""
    class Meta:
        """Model and field definitions"""
        model = models.Game
        fields = (
            'id', 'slug', 'name'
        )

class ShaderCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ShaderCache
        fields = ('url', 'updated_at')

class InstallerSerializer(serializers.ModelSerializer):
    """Serializer for Installers"""
    script = serializers.ReadOnlyField(source='raw_script')
    game_id = serializers.PrimaryKeyRelatedField(read_only=True)
    game_slug = serializers.ReadOnlyField(source='game.slug')
    name = serializers.ReadOnlyField(source='game.name')
    year = serializers.ReadOnlyField(source='game.year')
    steamid = serializers.ReadOnlyField(source='game.steamid')
    gogid = serializers.ReadOnlyField(source='game.gogid')
    gogslug = serializers.ReadOnlyField(source='game.gogslug')
    humbleid = serializers.ReadOnlyField(source='game.humbleid')
    humblestoreid = serializers.ReadOnlyField(source='game.humbleid')
    humblestoreid_real = serializers.ReadOnlyField(source='game.humblestoreid')
    # Adding Discord ID for Rich Presence Client
    discord_id = serializers.ReadOnlyField(source='game.discord_id', allow_null=True)

    user = serializers.StringRelatedField()

    runner = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        """Model and field definitions"""
        model = models.Installer
        fields = (
            'id', 'game_id', 'game_slug', 'name', 'year', 'user', 'runner', 'slug',
            'version', 'description', 'notes', 'credits', 'created_at', 'updated_at', 'draft',
            'published', 'published_by', 'rating', 'is_playable', 'steamid', 'gogid', 'gogslug',
            'humbleid', 'humblestoreid', 'humblestoreid_real', 'script', 'content',
            'discord_id',
        )

class InstallerHistorySerializer(serializers.ModelSerializer):
    """Serializer for Installers History"""
    runnername = serializers.ReadOnlyField(source='runner.name')
    user = serializers.StringRelatedField()

    class Meta:
        """Model and field definitions"""
        model = models.InstallerHistory
        fields = (
            'id', 'version', 'description', 'notes', 'content', 'created_at', 'installer_id', 'runnername', 'user',
        )

class InstallerDraftSerializer(serializers.ModelSerializer):
    """Serializer for Installers"""
    script = serializers.ReadOnlyField(source='raw_script')
    game = MicroGameSerializer()
    game_slug = serializers.ReadOnlyField(source='game.slug')
    name = serializers.ReadOnlyField(source='game.name')
    year = serializers.ReadOnlyField(source='game.year')
    steamid = serializers.ReadOnlyField(source='game.steamid')
    gogid = serializers.ReadOnlyField(source='game.gogid')
    gogslug = serializers.ReadOnlyField(source='game.gogslug')
    humbleid = serializers.ReadOnlyField(source='game.humbleid')
    humblestoreid = serializers.ReadOnlyField(source='game.humbleid')
    humblestoreid_real = serializers.ReadOnlyField(source='game.humblestoreid')
    # Adding Discord ID for Rich Presence Client
    discord_id = serializers.ReadOnlyField(source='game.discord_id', allow_null=True)

    user = serializers.StringRelatedField()

    runner = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    base_installer = InstallerSerializer()

    class Meta:
        """Model and field definitions"""
        model = models.InstallerDraft
        fields = (
            'id', 'game', 'game_slug', 'name', 'year', 'user', 'runner', 'slug',
            'version', 'description', 'notes', 'credits', 'created_at', 'draft',
            'steamid', 'gogid', 'gogslug',
            'humbleid', 'humblestoreid', 'humblestoreid_real', 'script', 'content',
            'discord_id', 'base_installer', 'review', 'reason'
        )

class GameSerializer(serializers.ModelSerializer):
    """Serializer for Games"""

    provider_games = ProviderGameSerializer(many=True)
    platforms = PlatformSerializer(many=True)
    aliases = GameAliasSerializer(many=True)
    shaders = ShaderCacheSerializer(many=True)
    change_for = MicroGameSerializer()

    class Meta:
        """Model and field definitions"""
        model = models.Game
        fields = (
            'id', 'name', 'slug', 'year', 'banner_url', 'icon_url', 'coverart',
            'platforms', 'provider_games', 'aliases', 'shaders', 'discord_id', 'change_for'
        )

class GameSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for game submissions"""
    game = GameSerializer()
    user = UserSerializer()
    class Meta:
        """Model and field definitions"""
        model = models.GameSubmission
        fields = ('id', 'user', 'game', 'created_at', 'accepted_at', 'reason',)


class GameDetailSerializer(GameSerializer):
    """A serializer for games with it's associated meta-data.
    Do not use in List views as it might cause performance issues.
    """
    genres = GenreSerializer(many=True)
    platforms = PlatformSerializer(many=True)
    aliases = GameAliasSerializer(many=True)
    installers = InstallerSerializer(many=True)
    shaders = ShaderCacheSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.Game
        fields = (
            'name', 'slug', 'year',
            'platforms', 'genres', 'aliases',
            'description', 'banner_url', 'icon_url', 'coverart', 'is_public',
            'updated', 'steamid', 'gogslug', 'humblestoreid', 'id',
            'user_count', 'installers', 'shaders',
            'discord_id',
        )


class GameLibrarySerializer(serializers.ModelSerializer):
    """Serializer for Games"""
    games = GameSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.GameLibrary
        fields = ('user', 'games')


class GameInstallersSerializer(GameSerializer):
    """Serializer for Installers belonging to a specific game"""
    installers = InstallerSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.Game
        fields = (
            'id', 'name', 'slug', 'year', 'platforms', 'genres',
            'banner_url', 'icon_url', 'is_public', 'updated',
            'steamid', 'gogid', 'gogslug', 'humblestoreid', 'installers'
        )


class InstallerIssueReplySerializer(serializers.ModelSerializer):
    """Serializer for Installer issues"""
    username = serializers.SerializerMethodField()

    class Meta:
        """Model and field definitions"""
        model = models.InstallerIssueReply
        fields = (
            'id',
            'issue',
            'username',
            'submitted_by',
            'submitted_on',
            'description'
        )

    def get_username(self, obj):  # pylint: disable=no-self-use
        """Return the username from the submitted_by field"""
        return obj.submitted_by.username


class InstallerIssueSerializer(serializers.ModelSerializer):
    """Serializer for installer issues"""
    replies = InstallerIssueReplySerializer(many=True, required=False)
    username = serializers.SerializerMethodField()

    class Meta:
        """Model and field definitions"""
        model = models.InstallerIssue
        fields = (
            'id',
            'installer',
            'username',
            'submitted_by',
            'submitted_on',
            'description',
            'solved',
            'replies'
        )

    def get_username(self, obj):  # pylint: disable=no-self-use
        """Return the username from the submitted_by field"""
        return obj.submitted_by.username


class InstallerIssueListSerializer(serializers.ModelSerializer):
    """Serializer for grouping all issues from a installer together"""
    issues = InstallerIssueSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.Installer
        fields = (
            'id',
            'slug',
            'version',
            'issues',
        )


class GameRelatedField(serializers.RelatedField):
    """A custom field to load games from generic relationship """

    def to_representation(self, value):
        """
        Serialize tagged objects to a simple textual representation.
        """
        if isinstance(value, models.Installer):
            serializer = InstallerSerializer(value)
            return serializer.data
        raise Exception('Unexpected type of tagged object')

    def to_internal_value(self, _value):
        """Raise an exception when trying to change back to internal values"""
        raise Exception("This field is read-only")


class ScreenshotSerializer(serializers.ModelSerializer):
    """Serializer for Screenshots"""
    game = MicroGameSerializer()
    uploaded_by = UserSerializer()
    class Meta:
        """Model and field definitions"""
        model = models.Screenshot
        fields = (
            'id',
            'game',
            'image',
            'uploaded_at',
            'uploaded_by',
            'description',
            'published'
        )