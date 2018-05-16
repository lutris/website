from django.views.generic import DetailView, ListView

from . import models


class BundleList(ListView):
    model = models.Bundle
    context_object_name = 'bundles'
    paginate_by = 25


class BundleDetail(DetailView):
    model = models.Bundle
    context_object_name = 'bundle'
