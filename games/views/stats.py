from __future__ import absolute_import

from rest_framework import filters, generics, permissions
from rest_framework.response import Response
from django.http import JsonResponse

from games import models, serializers


class SetStatView(generics.GenericAPIView):

    def get(self, request, stat_id, value):
        return JsonResponse({'message':'stat was set'})

class GetStatView(generics.GenericAPIView):

    def get(self, request, username, stat_id):
        return JsonResponse({'value': 75,
                              'stat':{'id': 54, 'type': "INT", 'name': "best score", 'increment_only': True,
                              'max_change': 0, 'min_change': 0, 'max_value': 100, 'window': 0,
                              'default_value': 0, 'aggregated': 0}})
