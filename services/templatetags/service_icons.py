"""
Template tags for rendering service category icons consistently
"""

from django import template

from services.icon_map import DEFAULT_ICON, ICONS

register = template.Library()


@register.simple_tag
def category_icon_class(category):
    """
    Get Font Awesome icon class for a category

    Usage: {% category_icon_class category %}
    Returns: "fa-hammer" (for example)
    """
    slug = getattr(category, "slug", "") or ""
    return ICONS.get(slug, DEFAULT_ICON)


@register.inclusion_tag("components/category_icon_lg.html")
def category_icon_lg(category):
    """
    Render large category icon (for cards)

    Usage: {% category_icon_lg category %}
    """
    slug = getattr(category, "slug", "") or ""
    icon_class = ICONS.get(slug, DEFAULT_ICON)
    return {"icon_class": icon_class, "category_name": category.name}


@register.inclusion_tag("components/category_icon_sm.html")
def category_icon_sm(category):
    """
    Render small category icon (for chips/list items)

    Usage: {% category_icon_sm category %}
    """
    slug = getattr(category, "slug", "") or ""
    icon_class = ICONS.get(slug, DEFAULT_ICON)
    return {"icon_class": icon_class, "category_name": category.name}
