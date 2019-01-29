"""Custom template tags and filters"""
from django import template

from common import util

register = template.Library()  # pylint: disable=invalid-name


@register.filter
def clean_html(markup):
    """Filter for removing most HTML tags from some markup."""
    return util.clean_html(markup)
