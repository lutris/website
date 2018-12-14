"""DRF serializers for Game models"""
# pylint: disable=too-few-public-methods
from rest_framework import serializers

from games import models
from platforms.models import Platform


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


class GameSerializer(serializers.ModelSerializer):
    """Serializer for Games"""
    genres = GenreSerializer(many=True)
    platforms = PlatformSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.Game
        fields = (
            'name', 'slug', 'year', 'platforms', 'genres',
            'banner_url', 'icon_url', 'is_public', 'updated', 'steamid',
            'gogslug', 'humblestoreid',
        )


class GameLibrarySerializer(serializers.ModelSerializer):
    """Serializer for Games"""
    games = GameSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.GameLibrary
        fields = ('user', 'games')


class InstallerSerializer(serializers.ModelSerializer):
    """Serializer for Installers"""
    script = serializers.ReadOnlyField(source='raw_script')
    game = serializers.HyperlinkedRelatedField(
        view_name='api_game_detail',
        read_only=True,
        lookup_field='slug'
    )
    game_slug = serializers.ReadOnlyField(source='game.slug')
    name = serializers.ReadOnlyField(source='game.name')
    year = serializers.ReadOnlyField(source='game.year')
    steamid = serializers.ReadOnlyField(source='game.steamid')
    gogid = serializers.ReadOnlyField(source='game.gogid')
    gogslug = serializers.ReadOnlyField(source='game.gogslug')
    humblestoreid = serializers.ReadOnlyField(source='game.humblestoreid')

    user = serializers.StringRelatedField()

    runner = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        """Model and field definitions"""
        model = models.Installer
        fields = ('id', 'game', 'game_slug', 'name', 'year', 'user', 'runner', 'slug',
                  'version', 'description', 'notes', 'created_at', 'updated_at', 'draft',
                  'published', 'published_by', 'rating', 'steamid', 'gogid', 'gogslug',
                  'humblestoreid', 'script', 'content')


class GameInstallersSerializer(GameSerializer):
    """Serializer for Installers belonging to a specific game"""
    installers = InstallerSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.Game
        fields = (
            'id', 'name', 'slug', 'year', 'platforms', 'genres',
            'banner_url', 'icon_url', 'is_public', 'updated',
            'steamid', 'godid', 'gogslug', 'humblestoreid', 'installers'
        )


class InstallerRevisionSerializer(serializers.Serializer):
    """Serializer for Installer revisions"""
    id = serializers.IntegerField()
    game = serializers.HyperlinkedRelatedField(
        view_name='api_game_detail',
        read_only=True,
        lookup_field='slug'
    )
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


class InstallerWithRevisionsSerializer(InstallerSerializer):
    """Serializer for Installers with their associated revisions"""
    revisions = InstallerRevisionSerializer(many=True)

    class Meta:
        """Model and field definitions"""
        model = models.Installer
        fields = ('id', 'game', 'user', 'runner', 'slug', 'version', 'description', 'draft',
                  'notes', 'created_at', 'updated_at', 'published', 'rating',
                  'script', 'content', 'revisions')


class GameRevisionSerializer(GameSerializer):
    """WAT"""
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

    def get_username(self, obj):
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

    def get_username(self, obj):
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
