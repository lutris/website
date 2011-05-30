from django.contrib.auth.forms import UserCreationForm
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django import forms

def register(request):
    form = UserCreationForm(request.POST)

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect('/')
    else:
        form = UserCreationForm()

    return render_to_response('accounts/register.html', {
        'form': form
        }, context_instance=RequestContext(request)
    )
    
