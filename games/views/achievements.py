from __future__ import absolute_import

from rest_framework import filters, generics, permissions
from rest_framework.response import Response
from django.http import JsonResponse

from games import models, serializers

class UnlockAchievementView(generics.GenericAPIView):

    def get(self, request, achievement_id):
        return JsonResponse({'message':'achievement was unlocked'})

class GetAchievementsView(generics.GenericAPIView):

    def get(self, request, username, achievement_id):
        return JsonResponse({
                              "achivements":
                              [
                                {
                                  'completed': True,
                                  'achievement':
                                  {
                                    'id': 101, 'name': "Win the game", 'Description': "Just win",
                                    'achieved_icon': "game/321/win.png", 'unachieved_icon': "game/321/win.png",
                                    'progress_stat':None
                                  }
                                },
                                {
                                  'completed': False,
                                  'achievement':
                                  {
                                    'id': 102, 'name': "Win 100 times", 'Description': "Just over and over again",
                                    'achieved_icon': "game/321/100wins.png", 'unachieved_icon': "game/321/100wins.png",
                                    'progress_stat':
                                    {
                                      'stat_id': 321, 'stat_name': "wins",'min_value': 0, 'max_value': 100, 'current_value': 56
                                    }
                                  }
                                }
                              ]
                            })
