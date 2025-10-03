import json
import stripe
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, FormView
from django.db import transaction
from django.utils import timezone
import logging

from .payment_models import PaymentIntent, PaymentMethod, StripeCustomer
from .models import CreditWallet

logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class CreatePaymentIntentView(LoginRequiredMixin, View):
    """Create a Stripe payment intent for wallet top-up"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            amount_cents = int(data.get('amount_cents', 0))
            
            # Validate amount (minimum 50 RON, maximum 5000 RON)
            if amount_cents < 5000 or amount_cents > 500000:
                return JsonResponse({
                    'error': 'Suma trebuie să fie între 50 și 5000 RON'
                }, status=400)
            
            # Get or create Stripe customer
            stripe_customer = StripeCustomer.get_or_create_for_user(request.user)
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='ron',
                customer=stripe_customer.stripe_customer_id,
                payment_method_types=['card'],
                metadata={
                    'user_id': request.user.id,
                    'purpose': 'wallet_topup'
                }
            )
            
            # Save payment intent to database
            payment_intent = PaymentIntent.objects.create(
                user=request.user,
                stripe_payment_intent_id=intent.id,
                amount_cents=amount_cents,
                client_secret=intent.client_secret,
                payment_method_types=intent.payment_method_types
            )
            
            return JsonResponse({
                'client_secret': intent.client_secret,
                'payment_intent_id': payment_intent.id
            })
            
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            return JsonResponse({
                'error': 'A apărut o eroare la procesarea plății'
            }, status=500)


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    """Handle successful payment"""
    template_name = 'services/payment_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        payment_intent_id = self.request.GET.get('payment_intent')
        if payment_intent_id:
            try:
                # Retrieve from Stripe
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                
                # Update local payment intent
                payment_intent = PaymentIntent.objects.get(
                    stripe_payment_intent_id=payment_intent_id,
                    user=self.request.user
                )
                
                if intent.status == 'succeeded' and payment_intent.status != 'succeeded':
                    payment_intent.mark_as_succeeded()
                    messages.success(
                        self.request, 
                        f'Plata de {payment_intent.amount_lei} RON a fost procesată cu succes!'
                    )
                
                context['payment_intent'] = payment_intent
                context['amount'] = payment_intent.amount_lei
                
            except (PaymentIntent.DoesNotExist, stripe.error.StripeError) as e:
                logger.error(f"Error retrieving payment intent: {str(e)}")
                messages.error(self.request, 'Nu am putut verifica statusul plății.')
        
        return context


class PaymentCancelView(LoginRequiredMixin, TemplateView):
    """Handle cancelled payment"""
    template_name = 'services/payment_cancel.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages.info(self.request, 'Plata a fost anulată.')
        return context


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """Handle Stripe webhooks"""
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            logger.error("Invalid payload in Stripe webhook")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature in Stripe webhook")
            return HttpResponse(status=400)
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            self._handle_payment_succeeded(payment_intent)
            
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            self._handle_payment_failed(payment_intent)
            
        else:
            logger.info(f"Unhandled Stripe event type: {event['type']}")
        
        return HttpResponse(status=200)
    
    def _handle_payment_succeeded(self, stripe_payment_intent):
        """Handle successful payment webhook"""
        try:
            payment_intent = PaymentIntent.objects.get(
                stripe_payment_intent_id=stripe_payment_intent['id']
            )
            
            if payment_intent.status != 'succeeded':
                payment_intent.mark_as_succeeded()
                logger.info(f"Payment succeeded: {payment_intent.stripe_payment_intent_id}")
                
        except PaymentIntent.DoesNotExist:
            logger.error(f"Payment intent not found: {stripe_payment_intent['id']}")
    
    def _handle_payment_failed(self, stripe_payment_intent):
        """Handle failed payment webhook"""
        try:
            payment_intent = PaymentIntent.objects.get(
                stripe_payment_intent_id=stripe_payment_intent['id']
            )
            
            payment_intent.mark_as_failed()
            logger.info(f"Payment failed: {payment_intent.stripe_payment_intent_id}")
            
        except PaymentIntent.DoesNotExist:
            logger.error(f"Payment intent not found: {stripe_payment_intent['id']}")


class PaymentMethodsView(LoginRequiredMixin, TemplateView):
    """Manage user's saved payment methods"""
    template_name = 'services/payment_methods.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_methods'] = PaymentMethod.objects.filter(
            user=self.request.user,
            is_active=True
        )
        return context


class DeletePaymentMethodView(LoginRequiredMixin, View):
    """Delete a saved payment method"""
    
    def post(self, request, payment_method_id):
        try:
            payment_method = get_object_or_404(
                PaymentMethod,
                id=payment_method_id,
                user=request.user
            )
            
            # Detach from Stripe customer
            stripe_customer = StripeCustomer.objects.get(user=request.user)
            stripe.PaymentMethod.detach(payment_method.stripe_payment_method_id)
            
            # Mark as inactive
            payment_method.is_active = False
            payment_method.save()
            
            messages.success(request, 'Metoda de plată a fost ștearsă.')
            
        except Exception as e:
            logger.error(f"Error deleting payment method: {str(e)}")
            messages.error(request, 'A apărut o eroare la ștergerea metodei de plată.')
        
        return redirect('services:payment_methods')


class WalletTopUpView(LoginRequiredMixin, TemplateView):
    """Enhanced wallet top-up page with Stripe integration"""
    template_name = 'services/wallet_topup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's wallet
        wallet, created = CreditWallet.objects.get_or_create(
            user=self.request.user,
            defaults={'balance_cents': 0}
        )
        
        context['wallet'] = wallet
        context['stripe_publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY
        
        # Predefined amounts
        context['predefined_amounts'] = [
            {'cents': 5000, 'lei': 50, 'leads': '~2-3'},
            {'cents': 10000, 'lei': 100, 'leads': '~5'},
            {'cents': 20000, 'lei': 200, 'leads': '~10'},
            {'cents': 50000, 'lei': 500, 'leads': '~25'},
        ]
        
        return context