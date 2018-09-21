import os

from django.utils import timezone
from django.conf import settings

from rest_framework import status
from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from common.permissions import IsAdminOrReadOnly
from runners.models import Runner, RunnerVersion, Runtime
from runners.serializers import RunnerSerializer, RuntimeSerializer


class RunnerListView(generics.ListAPIView):
    serializer_class = RunnerSerializer
    queryset = Runner.objects.all()
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name', )


class RunnerDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = RunnerSerializer
    lookup_field = 'slug'
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
    lookup_field = 'slug'
    queryset = Runner.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAdminOrReadOnly, )

    @staticmethod
    def upload(request):
        """Handles the file upload

        Return:
            The runner's public URL
        """
        uploaded_file = request.data['file']
        runner_dir = os.path.join(settings.FILES_ROOT, 'runners/')
        if not os.path.isdir(runner_dir):
            os.makedirs(runner_dir)
        dest_file_path = os.path.join(runner_dir, uploaded_file.name)

        with open(dest_file_path, 'wb') as runner_file:
            for chunk in uploaded_file.chunks():
                runner_file.write(chunk)

        return settings.FILES_URL + 'runners/' + uploaded_file.name

    def post(self, request, slug):
        try:
            runner = Runner.objects.get(slug=slug)
        except Runner.DoesNotExist:
            return Response(status=404)
        serializer = RunnerSerializer(runner)
        if 'file' in self.request.data:
            url = self.upload(request)
        else:
            url = self.data['url']
        runner_version = RunnerVersion.objects.create(
            runner=runner,
            version=request.data['version'],
            architecture=request.data['architecture'],
            url=url
        )
        runner_version.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class RuntimeView(generics.ListCreateAPIView):
    serializer_class = RuntimeSerializer
    queryset = Runtime.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAdminOrReadOnly, )

    def get(self, request):  # pylint: disable=W0221
        queryset = self.get_queryset()
        serializer = RuntimeSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):  # pylint: disable=W0221
        uploaded_file = request.data['file']
        runtime_dir = os.path.join(settings.FILES_ROOT, 'runtime/')
        if not os.path.isdir(runtime_dir):
            os.makedirs(runtime_dir)
        dest_file_path = os.path.join(runtime_dir, uploaded_file.name)

        with open(dest_file_path, 'wb') as runtime_file:
            for chunk in uploaded_file.chunks():
                runtime_file.write(chunk)

        runtime, created = Runtime.objects.get_or_create(
            name=request.data['name'],
            url=settings.FILES_URL + 'runtime/' + uploaded_file.name
        )
        runtime.created_at = timezone.now()
        runtime.save()
        serializer = RuntimeSerializer(runtime)

        if created:
            response_status = status.HTTP_201_CREATED
        else:
            response_status = status.HTTP_200_OK

        return Response(serializer.data, status=response_status)
