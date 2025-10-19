"""
Custom template filters for time-related formatting.
"""

from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()


@register.filter
def compact_timesince(value):
    """
    Returnează timpul scurs într-un format compact.

    Exemple:
        - 5 minute → "5m"
        - 45 minute → "45m"
        - 3 ore → "3h"
        - 2 zile → "2 zile"
        - 3 săptămâni → "3 săpt"
        - 5 luni → "5 luni"
        - 2 ani → "2 ani"

    Args:
        value: datetime object

    Returns:
        str: Formatted compact time string
    """
    if not value:
        return ""

    now = timezone.now()

    # Handle naive datetimes
    if timezone.is_naive(value):
        value = timezone.make_aware(value)

    diff = now - value

    # Sub 1 oră: afișează minute
    if diff < timedelta(hours=1):
        minutes = max(1, int(diff.total_seconds() / 60))  # Minimum 1m
        return f"{minutes}m"

    # Sub 24 ore: afișează ore
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h"

    # Sub 7 zile: afișează zile
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} {'zi' if days == 1 else 'zile'}"

    # Sub 30 zile: afișează săptămâni
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f"{weeks} săpt"

    # Sub 365 zile: afișează luni
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f"{months} {'lună' if months == 1 else 'luni'}"

    # Peste 1 an: afișează ani
    else:
        years = diff.days // 365
        return f"{years} {'an' if years == 1 else 'ani'}"
