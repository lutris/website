from __future__ import absolute_import

from rest_framework import filters, generics, permissions
from rest_framework.response import Response
from django.http import JsonResponse

from games import models, serializers


class AchievementsView(generics.GenericAPIView):

    def get(self, request):
        return JsonResponse({'foo':'bar'})
