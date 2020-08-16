"""DRF serializers for Game models"""
# pylint: disable=too-few-public-methods
import logging
from rest_framework import serializers
from reversion.models import Version, Revision

from games import models
from platforms.models import Platform

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

    user = serializers.StringRelatedField()

    runner = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        """Model and field definitions"""
        model = models.Installer
        fields = ('id', 'game_id', 'game_slug', 'name', 'year', 'user', 'runner', 'slug',
                  'version', 'description', 'notes', 'created_at', 'updated_at', 'draft',
                  'published', 'published_by', 'rating', 'steamid', 'gogid', 'gogslug',
                  'humbleid', 'humblestoreid', 'humblestoreid_real', 'script', 'content')


class InstallerRevisionSerializer(serializers.Serializer):
    """Serializer for Installer revisions
    This is not a ModelSerializer and is not directly mapped to revisions.
    Use RevisionSerializer for that.
    """
    id = serializers.IntegerField()
    game_id = serializers.PrimaryKeyRelatedField(read_only=True)
    game_slug = serializers.ReadOnlyField(source='game.slug')
    name = serializers.ReadOnlyField(source='game.name')
    year = serializers.ReadOnlyField(source='game.year')
    user = serializers.StringRelatedField()
    runner = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    slug = serializers.CharField()
    version = serializers.CharField()
    description = serializers.CharField()
    notes = serializers.CharField()
    created_at = serializers.DateTimeField()
    draft = serializers.BooleanField()
    published = serializers.BooleanField()
    rating = serializers.CharField()

    steamid = serializers.ReadOnlyField(source='game.steamid')
    gogid = serializers.ReadOnlyField(source='game.gogid')
    gogslug = serializers.ReadOnlyField(source='game.gogslug')
    humblestoreid = serializers.ReadOnlyField(source='game.humblestoreid')

    script = serializers.JSONField()
    content = serializers.CharField()
    reason = serializers.CharField()
    comment = serializers.CharField()
    installer_id = serializers.IntegerField()
    revision_id = serializers.IntegerField()

    def update(self, instance, validated_data):
        """That should probably be a valid call at some point"""
        LOGGER.error("Not supposed to do that")

    def create(self, validated_data):
        """That should probably be a valid call at some point"""
        LOGGER.error("Not supposed to do that")


class InstallerWithRevisionsSerializer(InstallerSerializer):
    """Serializer for Installers with their associated revisions
    Used by GameRevisionSerializer
    """
    revisions = InstallerRevisionSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.Installer
        fields = ('id', 'game', 'user', 'runner', 'slug', 'version', 'description', 'draft',
                  'notes', 'created_at', 'updated_at', 'published', 'rating',
                  'script', 'content', 'revisions')


class GameSerializer(serializers.ModelSerializer):
    """Serializer for Games"""

    class Meta:
        """Model and field definitions"""
        model = models.Game
        fields = (
            'name', 'slug', 'year',
            'description', 'banner_url', 'icon_url', 'is_public',
            'updated', 'steamid', 'gogid', 'gogslug', 'humblestoreid', 'id'
        )

class GameDetailSerializer(GameSerializer):
    """A serializer for games with it's associated meta-data.
    Do not use in List views as it might cause performance issues.
    """
    genres = GenreSerializer(many=True)
    platforms = PlatformSerializer(many=True)
    aliases = GameAliasSerializer(many=True)
    installers = InstallerWithRevisionsSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.Game
        fields = (
            'name', 'slug', 'year',
            'platforms', 'genres', 'aliases',
            'description', 'banner_url', 'icon_url', 'is_public',
            'updated', 'steamid', 'gogslug', 'humblestoreid', 'id',
            'user_count', 'installers'
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


class GameRevisionSerializer(GameSerializer):
    """API view used to fetch all installers and their related revisions for a given
    game.
    This is used in the moderator dashboard to load all revisions for a game in a
    single query.
    """
    installers = InstallerWithRevisionsSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.Game
        fields = (
            'name', 'slug', 'year', 'platforms', 'genres',
            'banner_url', 'icon_url', 'is_public', 'updated', 'steamid',
            'gogid', 'gogslug', 'humblestoreid', 'installers'
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


class VersionSerializer(serializers.ModelSerializer):
    """Serializer for revision versions
    Used in the RevisionSerializer
    """
    object = GameRelatedField(read_only=True)

    class Meta:
        """Model and field definitions"""
        model = Version
        fields = (
            'id',
            'revision_id',
            'object',
            'object_id',
            'format',
            'serialized_data',
        )


class RevisionSerializer(serializers.ModelSerializer):
    """Serializer for installer revision raw objects
    Used in the revision list view for the mod dashboard.
    """
    version_set = VersionSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = Revision
        fields = (
            'id',
            'user_id',
            'comment',
            'version_set'
        )
