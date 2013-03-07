from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from django.shortcuts import render


def register(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return HttpResponseRedirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})
