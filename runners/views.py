from rest_framework import generics, filters
from .models import Runner
from .serializers import RunnerSerializer


class RunnerListView(generics.ListAPIView):
    serializer_class = RunnerSerializer
    queryset = Runner.objects.all()
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name', )


class RunnerDetailView(generics.RetrieveAPIView):
    serializer_class = RunnerSerializer
    lookup_field = 'slug'
    queryset = Runner.objects.all()
