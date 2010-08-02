# Create your views here.
from django.template.context import RequestContext
#from django.http import HttpResponse
from django.shortcuts import render_to_response

def index(request):
    return render_to_response('games/index.html', {}, RequestContext(request))

def show(request):
    return render_to_response('games/show.html', {}, RequestContext(request))

