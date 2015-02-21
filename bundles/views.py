from . import models
from django.views.generic import ListView, DetailView


class BundleList(ListView):
    model = models.Bundle
    context_object_name = 'bundles'
    paginate_by = 25


class BundleDetail(DetailView):
    model = models.Bundle
    context_object_name = 'bundle'
