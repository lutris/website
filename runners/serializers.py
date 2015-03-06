from rest_framework import serializers
from .models import Runner, RunnerVersion


class RunnerVersionSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = RunnerVersion
        fields = ('version', 'path')


class RunnerSerializer(serializers.ModelSerializer):
    versions = RunnerVersionSerializer(many=True)

    class Meta(object):
        model = Runner
        fields = ('name', 'slug', 'icon', 'website', 'versions')
