from django.shortcuts import render
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.conf import settings


def example_email(request):
    context = {
        'email_title': "The email title"
    }
    return render(request, 'emails/example.html', context)


@login_required
def email_sender_test(request):
    user = request.user
    message = None
    if not user.is_superuser:
        raise Http404
    if request.method == 'POST':
        email = request.POST['email']
        body = "Mail sent to %s" % email
        send_mail("Email test", body, settings.DEFAULT_FROM_EMAIL, [email])
        message = 'The email was successfully sent to %s' % email
    return render(request, 'emails/email_sender_test.html', {'message': message})
