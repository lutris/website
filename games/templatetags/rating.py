from django import template
from django.utils.safestring import mark_safe
register = template.Library()


@register.simple_tag(takes_context=True)
def rating(context):
    from games.models import Installer
    installer = context['installer']
    if not installer.rating:
        return
    rating = installer.rating
    try:
        rating_text = Installer.RATINGS[rating]
    except KeyError:
        return
    return mark_safe(
        "<p class='rating'>"
        "<i class='rating-{}'></i>"
        "<span>{}</span>"
        "</p>".format(rating, rating_text)
    )
