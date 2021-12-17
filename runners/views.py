# pylint: disable=missing-docstring, too-many-ancestors
import os

from django.utils import timezone
from django.conf import settings
from django.views.generic import ListView
from django.http import Http404

from rest_framework import status
from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from common.permissions import IsAdminOrReadOnly
from runners.models import Runner, RunnerVersion, Runtime, RuntimeComponent
from runners.serializers import RunnerSerializer, RuntimeSerializer, RuntimeDetailSerializer
from games.models import Game


class RunnerListView(generics.ListAPIView):
    serializer_class = RunnerSerializer
    queryset = Runner.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)


class RunnerDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = RunnerSerializer
    lookup_field = "slug"
    queryset = Runner.objects.all()

    def get(self, request, slug):  # pylint: disable=W0221
        try:
            runner = Runner.objects.get(slug=slug)
        except Runner.DoesNotExist:
            return Response(status=404)
        serializer = RunnerSerializer(runner)
        return Response(serializer.data)


class RunnerUploadView(generics.CreateAPIView):
    serializer_class = RunnerSerializer
    lookup_field = "slug"
    queryset = Runner.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAdminOrReadOnly,)

    @staticmethod
    def upload(request):
        """Handles the file upload

        Return:
            The runner's public URL
        """
        uploaded_file = request.data["file"]
        runner_dir = os.path.join(settings.FILES_ROOT, "runners/")
        if not os.path.isdir(runner_dir):
            os.makedirs(runner_dir)
        dest_file_path = os.path.join(runner_dir, uploaded_file.name)

        with open(dest_file_path, "wb") as runner_file:
            for chunk in uploaded_file.chunks():
                runner_file.write(chunk)

        return settings.FILES_URL + "runners/" + uploaded_file.name

    def post(self, request, slug, *args, **kwargs):  # pylint: disable=arguments-differ
        try:
            runner = Runner.objects.get(slug=slug)
        except Runner.DoesNotExist:
            return Response(status=404)
        serializer = RunnerSerializer(runner)
        if "url" in request.data:
            url = request.data["url"]
        else:
            url = self.upload(request)
        runner_version = RunnerVersion.objects.create(
            runner=runner,
            version=request.data["version"],
            architecture=request.data["architecture"],
            url=url,
        )
        runner_version.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RuntimeListView(generics.ListCreateAPIView):
    serializer_class = RuntimeSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        """Match lutris games against service appids"""
        queryset = Runtime.objects.all()
        filter_enabled = self.request.GET.get('enabled')
        if filter_enabled:
            return queryset.filter(enabled=True)
        return queryset

    def get(self, request):  # pylint: disable=W0221
        queryset = self.get_queryset()
        serializer = RuntimeSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):  # pylint: disable=W0221
        runtime, created = Runtime.objects.get_or_create(
            name=request.data["name"], url=request.data["url"]
        )
        runtime.created_at = timezone.now()
        runtime.save()
        serializer = RuntimeSerializer(runtime)

        if created:
            response_status = status.HTTP_201_CREATED
        else:
            response_status = status.HTTP_200_OK

        return Response(serializer.data, status=response_status)


class RuntimeLegacyListView(RuntimeListView):
    queryset = Runtime.objects.exclude(url="")


class RuntimeDetailView(generics.RetrieveAPIView):
    """View the details of a runtime item with all its indiviual components"""
    serializer_class = RuntimeDetailSerializer
    queryset = Runtime.objects.all()
    lookup_field = "name"
    permission_classes = (IsAdminOrReadOnly, )

    def post(self, request, name):
        """POST creates a new component in the current runtime item"""
        try:
            runtime = Runtime.objects.get(name=name)
        except Runtime.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        url = request.data.get("url")
        filename = request.data.get("filename")
        if not url or not filename:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        component, _created = RuntimeComponent.objects.get_or_create(
            runtime=runtime,
            filename=filename
        )
        component.url = url
        component.save()
        return Response("", status=status.HTTP_201_CREATED)


class RunnersList(ListView):
    model = Runner
    context_object_name = "runners"


class RunnerGameList(ListView):
    model = Game
    context_object_name = "games"
    paginate_by = 25
    template_name = "runners/game_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
            installers__runner__slug=self.kwargs["runner"]
        ).distinct()

    def get_context_data(self, *, object_list=None, **kwargs):
        """Get the context for this view"""
        context = super().get_context_data(object_list=object_list, **kwargs)
        try:
            context["runner"] = Runner.objects.get(slug=self.kwargs["runner"])
        except Runner.DoesNotExist:
            raise Http404
        return context


class RunnerVersionGameList(ListView):
    model = Game
    context_object_name = "games"
    paginate_by = 25
    template_name = "runners/game_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(
            installers__runner__slug=self.kwargs["runner"],
            installers__content__icontains="  version: %s" % self.kwargs["version"],
        ).distinct()

    def get_context_data(self, *, object_list=None, **kwargs):
        """Get the context for this view"""
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["version"] = self.kwargs["version"]
        try:
            context["runner"] = Runner.objects.get(slug=self.kwargs["runner"])
        except Runner.DoesNotExist:
            raise Http404
        return context
