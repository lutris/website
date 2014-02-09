from django import template

from games import models

register = template.Library()


@register.inclusion_tag('includes/latest_games.html', takes_context=True)
def latest_games(context):
    games = models.Game.objects.published().order_by('-created')[:6]
    context['latest_games'] = games
    return context
