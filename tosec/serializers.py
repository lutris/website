"""Serializers for TOSEC"""
from rest_framework import serializers
from .models import Category, Game, Rom


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'description', 'category',
                  'version', 'author', 'section')


class RomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rom


class GameSerializer(serializers.ModelSerializer):
    roms = RomSerializer(many=True)
    category = CategorySerializer()

    class Meta:
        model = Game
        fields = ('name', 'description', 'category', 'roms')
