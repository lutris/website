from rest_framework import serializers

from bundles.models import Bundle
from games.serializers import GameSerializer


class BundleSerializer(serializers.ModelSerializer):
    """Serializer for Games"""

    games = GameSerializer(many=True)

    class Meta:
        """Model and field definitions"""

        model = Bundle
        fields = (
            "id",
            "name",
            "slug",
            "created_at",
            "games",
        )
