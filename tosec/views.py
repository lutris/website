"""TOSEC API views"""
from rest_framework import generics, filters
from tosec.models import TosecCategory, TosecGame
from tosec.serializers import CategorySerializer, GameSerializer


class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    queryset = TosecCategory.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', )
    paginate_by = 100


class GameListView(generics.ListAPIView):
    serializer_class = GameSerializer
    queryset = TosecGame.objects.all()
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name', )
    paginate_by = 100
