"""Custom template tags and filters"""
import math
from datetime import datetime
from django import template

from common import util

register = template.Library()  # pylint: disable=invalid-name
NO_PLAYTIME = ""

@register.filter
def clean_html(markup):
    """Filter for removing most HTML tags from some markup."""
    return util.clean_html(markup)


@register.filter
def human_time(playtime):
    if not playtime:
        return NO_PLAYTIME

    hours = math.floor(playtime)
    hours_unit = "hour" if hours == 1 else "hours"
    hours_text = f"{hours} {hours_unit}" if hours > 0 else ""

    minutes = int(round((playtime - hours) * 60, 0))
    minutes_unit = "minute" if minutes == 1 else "minutes"
    minutes_text = f"{minutes} {minutes_unit}" if minutes > 0 else ""

    formatted_time = " ".join([text for text in (hours_text, minutes_text) if text])
    if formatted_time:
        return formatted_time
    if playtime:
        return "Less than a minute"
    return NO_PLAYTIME

@register.filter
def tsdate(timestamp):
    date = datetime.fromtimestamp(timestamp)
    return date.strftime("%b %-d %Y")