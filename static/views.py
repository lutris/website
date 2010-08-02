from django.template.context import RequestContext
#from django.http import HttpResponse
from django.shortcuts import render_to_response

def index(request):
    return render_to_response('index.html', {}, RequestContext(request))

def contribute(request):
    return render_to_response('static/contribute.html', {}, RequestContext(request))

def download(request):
    return render_to_response('static/download.html', {}, RequestContext(request))
