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


def q_public_orders():
    """
    Returns Q object for public orders (not direct requests).
    Public orders are orders with no assigned_craftsman and published status.
    """
    return Q(
        assigned_craftsman__isnull=True,  # Not a direct request
        status="published"  # Only published orders
    )


def q_active_craftsmen():
    """
    Returns Q object for craftsmen who can appear in public listings.
    Uses permissive filtering - only requires active user account.
    Profile is_active field is not required for listings (allows new profiles to be visible).
    """
    return Q(
        user__is_active=True  # Only requirement: User account is active
    )
    # Note: Removed both is_verified and is_active requirements for maximum visibility
    # - is_verified: Too restrictive, verification badge shown in UI instead
    # - is_active: New craftsmen profiles should be visible even before full activation
    # Craftsmen can still control visibility via user account activation
