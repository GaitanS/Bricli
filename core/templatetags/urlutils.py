"""
Template tags for URL utilities
"""

from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag
def url_if_exists(name, *args, **kwargs):
    """
    Reverse URL by name, but return empty string if URL doesn't exist.

    Usage in templates:
        {% url_if_exists 'two_factor:setup' %}
        {% url_if_exists 'two_factor_setup' %}

    Args:
        name: URL pattern name
        *args: Positional arguments for reverse()
        **kwargs: Keyword arguments for reverse()

    Returns:
        URL string if exists, empty string otherwise
    """
    try:
        return reverse(name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return ""
