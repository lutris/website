from rest_framework import generics, filters
from tosec.models import Category, Game
from tosec.serializers import CategorySerializer, GameSerializer


class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', )
    paginate_by = 100


class GameListView(generics.ListAPIView):
    serializer_class = GameSerializer
    queryset = Game.objects.all()
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name', )
    paginate_by = 100
