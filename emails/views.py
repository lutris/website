from django.shortcuts import render


def example_email(request):
    context = {
        'email_title': "The email title"
    }
    return render(request, 'emails/example.html', context)
