"""
Testimonials templatetag - Load real reviews from database
"""
from django import template
from django.utils.module_loading import import_string

register = template.Library()


def _get_review_model():
    """Dynamically find the Review model from multiple possible app locations"""
    for path in (
        "services.models.Review",
        "accounts.models.Review",
        "reviews.models.Review",
    ):
        try:
            return import_string(path)
        except (ImportError, AttributeError):
            continue
    return None


@register.inclusion_tag("components/testimonials.html", takes_context=True)
def render_testimonials(context, limit=6):
    """
    Fetch and render real testimonials from Review model.
    Filters by rating >= 4 (since no is_approved field exists).
    Falls back gracefully if Review model doesn't exist or query fails.
    """
    Review = _get_review_model()
    reviews = []

    if Review:
        try:
            reviews = list(
                Review.objects.filter(rating__gte=4)
                .select_related("client", "craftsman", "craftsman__user")
                .order_by("-created_at")[:limit]
            )
        except Exception:
            # Gracefully handle any query errors
            reviews = []

    return {"reviews": reviews}
