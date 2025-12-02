from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ICONS = {
    'constructii': 'fa-hard-hat',
    'instalatii': 'fa-tools',
    'electrice': 'fa-bolt',
    'amenajari': 'fa-paint-roller',
    'curatenie': 'fa-broom',
    'gradinarit': 'fa-leaf',
    'auto': 'fa-car',
    'electrocasnice': 'fa-plug',
    'mobila': 'fa-couch',
    'acoperisuri': 'fa-home',
    'isolatii': 'fa-temperature-low',
}

@register.simple_tag
def service_icon(slug):
    """
    Returns a FontAwesome icon for a given category slug.
    """
    icon_class = ICONS.get(slug, 'fa-hammer') # Default icon
    return mark_safe(f'<i class="fas {icon_class}"></i>')
