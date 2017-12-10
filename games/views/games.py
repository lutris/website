from __future__ import absolute_import

from rest_framework import filters, generics, permissions
from rest_framework.response import Response

from games import models, serializers


class GameListView(generics.GenericAPIView):
    filter_backends = (filters.SearchFilter, )
    search_fields = ('slug', 'name')

    def get_queryset(self):
        if 'games' in self.request.GET:
            game_slugs = self.request.GET.getlist('games')
        elif 'games' in self.request.data:
            game_slugs = self.request.data.get('games')
        else:
            game_slugs = []
        if game_slugs:
            queryset = models.Game.objects.filter(change_for__isnull=True, slug__in=game_slugs)
        elif 'random' in self.request.GET:
            queryset = [models.Game.objects.get_random(self.request.GET['random'])]
        else:
            queryset = models.Game.objects.filter(change_for__isnull=True)
        return queryset

    def get_serializer_class(self):
        if self.request.GET.get('installers') == '1':
            return serializers.GameInstallersSerializer
        else:
            return serializers.GameSerializer

    def get(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Using POST instead of GET is a violation of API rules but it's the
        # only way to send a huge payload to the server. GET querystrings only
        # support a limited number of characters (depending on the web server or
        # the browser used) whereas POST request do not have this limitation.
        return self.get(request)


class GameLibraryView(generics.RetrieveAPIView):
    serializer_class = serializers.GameLibrarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, username):
        try:
            library = models.GameLibrary.objects.get(user__username=username)
        except models.GameLibrary.DoesNotExist:
            return Response(status=404)
        serializer = serializers.GameLibrarySerializer(library)
        return Response(serializer.data)


class GameDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.GameSerializer
    lookup_field = 'slug'
    queryset = models.Game.objects.filter(change_for__isnull=True)


class GameInstallersView(generics.RetrieveAPIView):
    serializer_class = serializers.GameInstallersSerializer
    lookup_field = 'slug'
    queryset = models.Game.objects.filter(change_for__isnull=True)
