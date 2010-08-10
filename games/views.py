# Create your views here.
from django.template.context import RequestContext
#from django.http import HttpResponse
from django.shortcuts import render_to_response
from lutrisweb.games.models import Game

def index(request):
    games = Game.objects.all()
    return render_to_response('games/index.html', {'games' : games}, RequestContext(request))

def show(request):
    return render_to_response('games/show.html', {}, RequestContext(request))
