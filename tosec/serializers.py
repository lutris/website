from rest_framework import serializers
from .models import Category, Game


class CategorySerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Category
        fields = ('name', 'description', 'category',
                  'version', 'author', 'section')


class GameSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Game
        fields = ('name', 'description', 'category')
