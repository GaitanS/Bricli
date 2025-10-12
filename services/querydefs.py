"""
Query definitions for robust filtering across different status naming schemes
"""
from django.db.models import Q


def q_completed():
    """
    Returns Q object for completed orders.
    Tries to use COMPLETED_STATUSES if defined on model, otherwise falls back to common values.
    """
    from services.models import Order

    completed = getattr(Order, "COMPLETED_STATUSES", None)
    if completed:
        return Q(status__in=completed)

    # Fallback to common values
    return Q(status__in=["completed", "done", "closed", "finalized"]) | Q(is_completed=True)


def q_active():
    """
    Returns Q object for active orders (not completed, not cancelled).
    Tries to use ACTIVE_STATUSES if defined, otherwise calculates as ~completed & ~cancelled.
    """
    from services.models import Order

    cancelled = getattr(Order, "CANCELLED_STATUSES", ["cancelled", "canceled", "refused"])

    # If active statuses are explicitly defined, use them
    active = getattr(Order, "ACTIVE_STATUSES", None)
    if active:
        return Q(status__in=active)

    # Otherwise: everything that's not completed and not cancelled
    return ~q_completed() & ~Q(status__in=cancelled)
