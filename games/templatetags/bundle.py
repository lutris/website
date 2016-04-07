from django import template
register = template.Library()


@register.inclusion_tag('includes/bundle_game_list.html')
def bundle_games(bundle_slug):
    from games.models import Bundle
    try:
        bundle = Bundle.object.get(slug=bundle_slug)
    except Bundle.DoesNotExist:
        bundle = None
    return {'bundle': bundle}
