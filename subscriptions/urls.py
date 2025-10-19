"""
Subscription URL patterns

BETA MODE: When SUBSCRIPTIONS_ENABLED = False, all subscription URLs are disabled
and will return 404. This allows us to hide subscription features during BETA launch
without deleting code.
"""

from django.urls import path
from django.conf import settings

from . import webhook_views, views

app_name = 'subscriptions'

# BETA MODE: Disable all subscription URLs when feature flag is off
if settings.SUBSCRIPTIONS_ENABLED:
    # Production mode: All subscription features available
    urlpatterns = [
        # Stripe webhook endpoint
        path('webhook/stripe/', webhook_views.stripe_webhook, name='stripe_webhook'),

        # Invoice views (Phase 5)
        path('facturi/', views.invoice_list, name='invoice_list'),
        path('facturi/<int:invoice_id>/pdf/', views.invoice_download_pdf, name='invoice_download_pdf'),

        # Subscription management views (Phase 7)
        path('preturi/', views.pricing, name='pricing'),
        path('date-fiscale/', views.fiscal_data, name='fiscal_data'),
        path('upgrade/<str:tier_name>/', views.upgrade, name='upgrade'),
        path('manage/', views.manage_subscription, name='manage'),
        path('cancel/', views.cancel_subscription, name='cancel_subscription'),
        path('rambursare/', views.request_refund, name='request_refund'),
        path('portal/', views.billing_portal, name='billing_portal'),
    ]
else:
    # BETA MODE: Empty urlpatterns - all subscription URLs return 404
    urlpatterns = []
