from django.views.generic import DetailView, ListView

from rest_framework import generics
from rest_framework.response import Response

from . import models, serializers


class BundleList(ListView):
    model = models.Bundle
    context_object_name = 'bundles'
    paginate_by = 25


class BundleDetail(DetailView):
    model = models.Bundle
    context_object_name = 'bundle'


class BundleView(generics.RetrieveAPIView):
    serializer_class = serializers.BundleSerializer

    def get(self, request, slug):
        try:
            bundle = models.Bundle.objects.get(slug=slug)
        except models.Bundle.DoesNotExist:
            return Response(status=404)
        serializer = serializers.BundleSerializer(bundle)
        return Response(serializer.data)
