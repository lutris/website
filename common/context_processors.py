from django.conf import settings

def discord_url(_request):
    return {'DISCORD_URL': settings.DISCORD_URL}
