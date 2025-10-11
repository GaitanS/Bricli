"""
Dictionary utility filters for Django templates.
Enables dictionary key access in templates.
"""

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Access dictionary item by key in templates.

    Usage:
        {{ rating_counts|get_item:5.0 }}
        {{ my_dict|get_item:'key_name' }}

    Args:
        dictionary: Dict to access
        key: Key to retrieve (can be string, int, float)

    Returns:
        Value at key, or None if key doesn't exist
    """
    if not dictionary:
        return None

    # Convert string key to float if it looks like a float
    try:
        float_key = float(key)
        if float_key in dictionary:
            return dictionary.get(float_key)
    except (ValueError, TypeError):
        pass

    # Try direct key access
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None


@register.filter
def split(value, delimiter=","):
    """
    Split a string by delimiter.

    Usage:
        {% for item in "5.0,4.5,4.0"|split:"," %}

    Args:
        value: String to split
        delimiter: Delimiter character (default: ",")

    Returns:
        List of strings
    """
    if not value:
        return []
    return [item.strip() for item in str(value).split(delimiter)]
