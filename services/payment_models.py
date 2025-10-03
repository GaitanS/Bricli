from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import stripe
from django.conf import settings

User = get_user_model()


class PaymentIntent(models.Model):
    """Model to track Stripe payment intents for wallet top-ups"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_intents')
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    amount_cents = models.PositiveIntegerField(help_text="Amount in cents")
    currency = models.CharField(max_length=3, default='RON')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    client_secret = models.CharField(max_length=500, blank=True)
    payment_method_types = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    succeeded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.stripe_payment_intent_id} - {self.amount_lei} RON - {self.status}"
    
    @property
    def amount_lei(self):
        """Convert cents to RON"""
        return self.amount_cents / 100
    
    def mark_as_succeeded(self):
        """Mark payment as succeeded and add credit to wallet"""
        if self.status != 'succeeded':
            self.status = 'succeeded'
            self.succeeded_at = timezone.now()
            self.save()
            
            # Add credit to user's wallet
            from .models import CreditWallet, WalletTransaction
            
            wallet, created = CreditWallet.objects.get_or_create(
                user=self.user,
                defaults={'balance_cents': 0}
            )
            
            wallet.add_amount(
                amount_cents=self.amount_cents,
                reason='top_up',
                meta={
                    'payment_intent_id': self.stripe_payment_intent_id,
                    'payment_method': 'stripe'
                }
            )
    
    def mark_as_failed(self):
        """Mark payment as failed"""
        self.status = 'failed'
        self.save()


class PaymentMethod(models.Model):
    """Store user's saved payment methods"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    stripe_payment_method_id = models.CharField(max_length=255, unique=True)
    
    # Card details (from Stripe)
    card_brand = models.CharField(max_length=50, blank=True)  # visa, mastercard, etc.
    card_last4 = models.CharField(max_length=4, blank=True)
    card_exp_month = models.PositiveSmallIntegerField(null=True, blank=True)
    card_exp_year = models.PositiveSmallIntegerField(null=True, blank=True)
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.card_brand.title()} **** {self.card_last4}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per user
        if self.is_default:
            PaymentMethod.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class StripeCustomer(models.Model):
    """Link Django users to Stripe customers"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stripe_customer')
    stripe_customer_id = models.CharField(max_length=255, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Stripe Customer for {self.user.username}"
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create Stripe customer for user"""
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            # Create Stripe customer
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            stripe_customer = stripe.Customer.create(
                email=user.email,
                name=user.get_full_name() or user.username,
                metadata={
                    'user_id': user.id,
                    'username': user.username
                }
            )
            
            return cls.objects.create(
                user=user,
                stripe_customer_id=stripe_customer.id
            )