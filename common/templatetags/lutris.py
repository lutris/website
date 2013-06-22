import copy

from django import template
from django.conf import settings

from games import models

register = template.Library()


def get_links(user_agent):
    systems = ['ubuntu', 'fedora', 'linux']
    downloads = copy.copy(settings.DOWNLOADS)
    main_download = None
    for system in systems:
        if system in user_agent:
            main_download = {system: settings.DOWNLOADS[system]}
            downloads.pop(system)
    if not main_download:
        main_download = {'linux': downloads.pop('linux')}
    return (main_download, downloads)


@register.inclusion_tag('includes/download_links.html', takes_context=True)
def download_links(context):
    request = context['request']
    user_agent = request.META['HTTP_USER_AGENT'].lower()
    context['main_download'], context['downloads'] = get_links(user_agent)
    return context


@register.inclusion_tag('includes/featured_slider.html', takes_context=True)
def featured_slider(context):
    context['featured_contents'] = models.Featured.objects.all()
    return context


@register.inclusion_tag('includes/latest_games.html', takes_context=True)
def latest_games(context):
    games = models.Game.objects.published().order_by('-created')[:5]
    context['latest_games'] = games
    return context
