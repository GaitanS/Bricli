"""
Template filters for Romanian text formatting
"""

from django import template

register = template.Library()


@register.filter
def mesters_for(category_name):
    """
    Returns correct Romanian heading for craftsmen list.

    Usage:
        {{ category.name|mesters_for }}
        Output: "Meșteri recomandați pentru electricieni"

    Args:
        category_name: Category name (can be string or None)

    Returns:
        Properly formatted heading in Romanian (masculine plural)
    """
    if not category_name:
        return "Meșteri recomandați"

    # Convert to lowercase for proper grammar
    category_lower = str(category_name).strip().lower()

    return f"Meșteri recomandați pentru {category_lower}"
