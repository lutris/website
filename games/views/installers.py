from __future__ import absolute_import
from rest_framework import generics

from common.permissions import IsAdminOrReadOnly
from games import serializers
from games import models


class InstallerListView(generics.ListAPIView):
    serializer_class = serializers.InstallerSerializer
    queryset = models.Installer.objects.all()


class InstallerDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = serializers.InstallerSerializer
    queryset = models.Installer.objects.all()
