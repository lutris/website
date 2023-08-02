# pylint: disable=missing-docstring, too-many-ancestors, no-member
import os

from django.utils import timezone
from django.conf import settings

from rest_framework import status
from rest_framework import generics, filters, views
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import APIException

from common.permissions import IsAdminOrReadOnly
from runners.models import Runner, RunnerVersion, Runtime, RuntimeComponent
from runners.serializers import RunnerSerializer, RuntimeSerializer, RuntimeDetailSerializer



class ClientTooOld(APIException):
    status_code = 426
    default_detail = 'Your Lutris client is out of date. Please upgrade.'
    default_code = 'client_out_of_date'

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


def get_version_number(version):
    """Return a decimal conversion of a version string"""
    version_parts = version.split(".")
    if len(version_parts) < 3:
        raise ValueError
    if len(version_parts) == 3:
        version_parts.append(0)
    release, major, minor, patch = version_parts[:4]
    return int(release) * 100000000 + int(major) * 1000000 + int(minor) * 1000 + int(patch)

class RuntimeListView(generics.ListCreateAPIView):
    serializer_class = RuntimeSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        """Match lutris games against service appids"""
        user_agent = self.request.META["HTTP_USER_AGENT"]
        version_number = 0
        if user_agent.startswith("Lutris"):
            remote_version = user_agent.split()[1]
            try:
                version_number = get_version_number(remote_version)
            except ValueError as ex:
                raise ClientTooOld from ex
            if version_number < 5011000:
                raise ClientTooOld

        queryset = Runtime.objects.all()
        if version_number:
            queryset = queryset.filter(min_version__lte=version_number)
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


class RuntimeVersions(views.APIView):
    def get(self, request):
        response = {
            "client_version": settings.CLIENT_VERSION,
            "runtimes": {},
            "runners": {},
        }
        user_agent = request.META["HTTP_USER_AGENT"]
        version_number = 0
        if user_agent.startswith("Lutris"):
            remote_version = user_agent.split()[1]
            try:
                version_number = get_version_number(remote_version)
            except ValueError as ex:
                raise ClientTooOld from ex
        for runner in Runner.objects.all():
            response["runners"][runner.slug] = [{
                "name": runner.slug,
                "version": version.version,
                "url": version.url,
                "architecture": version.architecture
            } for version in runner.runner_versions.filter(default=True)]
        for runtime in Runtime.objects.filter(enabled=True):
            if version_number and runtime.min_version and version_number < runtime.min_version:
                continue
            response["runtimes"][runtime.name] = {
                "name": runtime.name,
                "created_at": runtime.created_at,
                "architecture": runtime.architecture,
                "url": runtime.url,
                "version": runtime.version,
                "versioned": runtime.versioned,
            }

        return Response(response)
