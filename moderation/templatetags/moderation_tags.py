"""
Template tags for moderation system
"""

from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()


@register.filter
def get_content_type_id(obj):
    """
    Returns the content type ID for an object
    """
    if obj:
        content_type = ContentType.objects.get_for_model(obj)
        return content_type.id
    return None


@register.filter
def can_report(user, obj):
    """
    Check if user can report this object
    """
    if not user.is_authenticated:
        return False

    # Users can't report their own content
    if hasattr(obj, "user") and obj.user == user:
        return False

    if hasattr(obj, "author") and obj.author == user:
        return False

    return True


@register.inclusion_tag("moderation/report_button_simple.html", takes_context=True)
def report_button(context, obj, button_class="btn-outline-secondary btn-sm"):
    """
    Renders a simple report button
    """
    user = context["user"]

    return {
        "user": user,
        "object": obj,
        "button_class": button_class,
        "can_report": can_report(user, obj),
        "content_type_id": get_content_type_id(obj),
    }


@register.inclusion_tag("moderation/quick_report_buttons.html", takes_context=True)
def quick_report_buttons(context, obj):
    """
    Renders quick report buttons (spam, inappropriate, etc.)
    """
    user = context["user"]

    return {
        "user": user,
        "object": obj,
        "can_report": can_report(user, obj),
        "content_type_id": get_content_type_id(obj),
    }
