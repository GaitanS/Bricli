"""
Star rating display template tags for search filters.
Renders 5-star displays with filled/empty stars.
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def stars_5(rating_threshold):
    """
    Render 5 stars with filled stars up to the rating threshold.

    Args:
        rating_threshold: Float (3.0, 3.5, 4.0, 4.5, 5.0)

    Returns:
        HTML string with Font Awesome star icons

    Examples:
        {% stars_5 4.0 %} -> ★★★★☆
        {% stars_5 4.5 %} -> ★★★★⯨
        {% stars_5 5.0 %} -> ★★★★★
    """
    try:
        threshold = float(rating_threshold)
    except (ValueError, TypeError):
        threshold = 0.0

    html_parts = []

    for star_num in range(1, 6):  # Stars 1-5
        if threshold >= star_num:
            # Full star
            html_parts.append('<i class="fas fa-star text-warning"></i>')
        elif threshold >= star_num - 0.5:
            # Half star
            html_parts.append('<i class="fas fa-star-half-alt text-warning"></i>')
        else:
            # Empty star
            html_parts.append('<i class="far fa-star text-muted"></i>')

    return mark_safe(''.join(html_parts))
