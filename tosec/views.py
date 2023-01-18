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
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name', )
    paginate_by = 100

    def get_queryset(self):
        md5sum = self.request.GET.get('md5')
        base_query = TosecGame.objects.all()
        if md5sum:
            base_query = base_query.filter(roms__md5__iexact=md5sum)
        return base_query