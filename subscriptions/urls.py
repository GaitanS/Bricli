"""
Subscription URL patterns
"""

from django.urls import path

from . import webhook_views, views

app_name = 'subscriptions'

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
