import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from .models import AuthToken


def register(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return HttpResponseRedirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def client_auth(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    if user and user.is_active:
        auth_token = AuthToken(user=user, ip_address=get_client_ip(request))
        response_data = {'token': auth_token.token}
    else:
        response_data = {'error': "Bad credentials"}

    return HttpResponse(json.dumps(response_data, mimetype="application/json"))
