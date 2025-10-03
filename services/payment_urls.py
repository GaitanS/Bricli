from django.urls import path
from . import payment_views

app_name = 'payments'

urlpatterns = [
    # Payment processing
    path('create-payment-intent/', 
         payment_views.CreatePaymentIntentView.as_view(), 
         name='create_payment_intent'),
    
    # Payment results
    path('success/', 
         payment_views.PaymentSuccessView.as_view(), 
         name='payment_success'),
    
    path('cancel/', 
         payment_views.PaymentCancelView.as_view(), 
         name='payment_cancel'),
    
    # Stripe webhook
    path('webhook/stripe/', 
         payment_views.StripeWebhookView.as_view(), 
         name='stripe_webhook'),
    
    # Payment methods management
    path('methods/', 
         payment_views.PaymentMethodsView.as_view(), 
         name='payment_methods'),
    
    path('methods/<int:payment_method_id>/delete/', 
         payment_views.DeletePaymentMethodView.as_view(), 
         name='delete_payment_method'),
    
    # Wallet top-up
    path('topup/', 
         payment_views.WalletTopUpView.as_view(), 
         name='wallet_topup'),
]