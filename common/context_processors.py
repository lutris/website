from django.conf import settings

def discord_url(request):
    return {'DISCORD_URL': settings.DISCORD_URL}
