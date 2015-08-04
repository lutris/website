import os
from django.conf import settings
from rest_framework import status
from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Runner, RunnerVersion
from .serializers import RunnerSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permission to allow only admins to make changes."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff is True


class RunnerListView(generics.ListAPIView):
    serializer_class = RunnerSerializer
    queryset = Runner.objects.all()
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name', )


class RunnerDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = RunnerSerializer
    lookup_field = 'slug'
    queryset = Runner.objects.all()

    def get(self, request, slug):
        queryset = self.get_queryset()[0]
        serializer = RunnerSerializer(queryset)
        return Response(serializer.data)


class RunnerUploadView(generics.CreateAPIView):
    serializer_class = RunnerSerializer
    lookup_field = 'slug'
    queryset = Runner.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAdminOrReadOnly, )

    def post(self, request, slug):
        try:
            runner = self.get_queryset()[0]
        except KeyError:
            return Response(status=404)
        serializer = RunnerSerializer(runner)
        runner_file = request.data['file']
        runner_dir = os.path.join(settings.FILES_ROOT, 'runners/')
        if not os.path.isdir(runner_dir):
            os.makedirs(runner_dir)
        dest_file_path = os.path.join(runner_dir, runner_file.name)

        uploaded_file = request.data['file']

        with open(dest_file_path, 'wb') as runner_file:
            for chunk in uploaded_file.chunks():
                runner_file.write(chunk)

        runner_version = RunnerVersion.objects.create(
            runner=runner,
            version=request.data['version'],
            architecture=request.data['architecture'],
            url=settings.FILES_URL + 'runners/' + uploaded_file.name
        )
        runner_version.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
