from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Category
        fields = ('name', 'description', 'category',
                  'version', 'author', 'section')
