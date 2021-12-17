from django.conf import settings

def discord_url(_request):
    return {'DISCORD_URL': settings.DISCORD_URL}


def dashboard_url(_request):
    return {'DASHBOARD_URL': settings.DASHBOARD_URL}