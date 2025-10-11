"""
Template tag for building query strings with parameter manipulation
"""

from urllib.parse import urlencode

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """
    Build a query string from request.GET, allowing parameter updates/removals.

    Usage in templates:
        {% querystring county='cluj' %}           # Set county=cluj
        {% querystring county=None %}             # Remove county param
        {% querystring q='test' county='cluj' %}  # Set multiple params

    Args:
        context: Django template context (provides request)
        **kwargs: Parameters to set/remove (None or empty string removes param)

    Returns:
        URL-encoded query string (without leading '?')
    """
    request = context.get("request")
    if not request:
        return ""

    # Copy existing GET parameters
    params = request.GET.copy()

    # Apply updates/removals
    for key, value in kwargs.items():
        if value is None or value == "":
            # Remove parameter
            params.pop(key, None)
        else:
            # Set parameter
            params[key] = value

    # Return encoded query string
    return urlencode(params, doseq=True)
