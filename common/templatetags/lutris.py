"""Custom template tags and filters"""
from django import template

from common import util
from games import models

register = template.Library()  # pylint: disable=invalid-name


@register.inclusion_tag('includes/latest_games.html', takes_context=True)
def latest_games(context):
    """Renders a list of latest games.
    This is weird and only used on the home page and probably has nothing to do
    in the common app.
    """
    games = models.Game.objects.with_installer().order_by('-created')[:6]
    context['latest_games'] = games
    return context


@register.filter
def clean_html(markup):
    """Filter for removing most HTML tags from some markup."""
    return util.clean_html(markup)
