"""
Subscription Views

Handles subscription management, pricing, upgrades, cancellation, and invoices.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.views.decorators.http import require_POST
import stripe

from .models import Invoice, CraftsmanSubscription, SubscriptionTier
from .smartbill_service import InvoiceService, SmartBillAPIError
from .services import SubscriptionService, SubscriptionError, MissingFiscalDataError
from .forms import FiscalDataForm, UpgradeConfirmationForm, CancelSubscriptionForm, RequestRefundForm

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def invoice_list(request):
    """
    List all invoices for the current craftsman.

    Returns:
        Rendered template with invoice list
    """
    # Ensure user is a craftsman
    if not hasattr(request.user, 'craftsman_profile'):
        raise PermissionDenied("Only craftsmen can view invoices")

    craftsman = request.user.craftsman_profile

    try:
        subscription = craftsman.subscription
        invoices = subscription.invoices.all().order_by('-created_at')
    except CraftsmanSubscription.DoesNotExist:
        invoices = []

    context = {
        'invoices': invoices,
    }

    return render(request, 'subscriptions/invoice_list.html', context)


@login_required
def invoice_download_pdf(request, invoice_id):
    """
    Download PDF of a specific invoice.

    Args:
        invoice_id: Invoice ID

    Returns:
        PDF file download response

    Raises:
        Http404: If invoice not found
        PermissionDenied: If user is not the invoice owner
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)

    # Ensure user owns this invoice
    if not hasattr(request.user, 'craftsman_profile'):
        raise PermissionDenied("Only craftsmen can download invoices")

    if invoice.subscription.craftsman != request.user.craftsman_profile:
        raise PermissionDenied("You can only download your own invoices")

    # Check if PDF is stored locally
    if invoice.pdf_file:
        # Serve local PDF
        response = HttpResponse(invoice.pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{invoice.get_download_filename()}"'
        return response
    else:
        # Download from Smart Bill API
        try:
            pdf_content = InvoiceService.get_invoice_pdf(
                series=invoice.smartbill_series,
                number=invoice.smartbill_number
            )

            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{invoice.get_download_filename()}"'
            return response

        except SmartBillAPIError as e:
            # Log error and show user-friendly message
            raise Http404(f"Could not retrieve invoice PDF: {e}")


# ============================================================================
# SUBSCRIPTION MANAGEMENT VIEWS (Phase 7)
# ============================================================================

def pricing(request):
    """
    Display subscription tiers and pricing.

    Public view - accessible to all users.
    """
    tiers = SubscriptionTier.objects.all().order_by('price')

    # Get current subscription if user is logged in craftsman
    current_subscription = None
    if request.user.is_authenticated and hasattr(request.user, 'craftsman_profile'):
        try:
            current_subscription = request.user.craftsman_profile.subscription
        except CraftsmanSubscription.DoesNotExist:
            pass

    context = {
        'tiers': tiers,
        'current_subscription': current_subscription,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY if hasattr(settings, 'STRIPE_PUBLISHABLE_KEY') else '',
    }

    return render(request, 'subscriptions/pricing.html', context)


@login_required
def fiscal_data(request):
    """
    Collect fiscal data required for invoicing.

    Mandatory before first upgrade to paid tier.
    """
    # Ensure user is a craftsman
    if not hasattr(request.user, 'craftsman_profile'):
        messages.error(request, 'Doar meseriașii pot completa date fiscale.')
        return redirect('core:home')

    craftsman = request.user.craftsman_profile
    next_url = request.GET.get('next', reverse('subscriptions:manage'))

    if request.method == 'POST':
        form = FiscalDataForm(request.POST, instance=craftsman)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datele fiscale au fost salvate cu succes!')
            return redirect(next_url)
    else:
        form = FiscalDataForm(instance=craftsman)

    context = {
        'form': form,
        'next_url': next_url,
    }

    return render(request, 'subscriptions/fiscal_data.html', context)


@login_required
def upgrade(request, tier_name):
    """
    Upgrade to a paid subscription tier.

    GET: Show payment form with Stripe Elements
    POST: Process upgrade with payment_method_id from Stripe
    """
    # Ensure user is a craftsman
    if not hasattr(request.user, 'craftsman_profile'):
        messages.error(request, 'Doar meseriașii pot face upgrade.')
        return redirect('core:home')

    craftsman = request.user.craftsman_profile

    # Get target tier
    try:
        tier = SubscriptionTier.objects.get(name=tier_name)
    except SubscriptionTier.DoesNotExist:
        messages.error(request, f'Planul "{tier_name}" nu există.')
        return redirect('subscriptions:pricing')

    if tier.name == 'free':
        messages.error(request, 'Nu poți face upgrade la planul gratuit.')
        return redirect('subscriptions:pricing')

    # Check current subscription
    try:
        subscription = craftsman.subscription
        if subscription.tier.price >= tier.price:
            messages.info(request, f'Deja ai un plan egal sau superior cu {tier.display_name}.')
            return redirect('subscriptions:manage')
    except CraftsmanSubscription.DoesNotExist:
        messages.error(request, 'Nu ai o subscriere activă.')
        return redirect('subscriptions:pricing')

    # Validate fiscal data exists
    try:
        SubscriptionService.validate_fiscal_data(craftsman)
    except MissingFiscalDataError as e:
        messages.warning(
            request,
            f'Trebuie să completezi datele fiscale înainte de upgrade: {e}'
        )
        return redirect(f"{reverse('subscriptions:fiscal_data')}?next={reverse('subscriptions:upgrade', args=[tier_name])}")

    if request.method == 'POST':
        form = UpgradeConfirmationForm(request.POST)
        if form.is_valid():
            payment_method_id = form.cleaned_data['payment_method_id']
            waive_withdrawal = form.cleaned_data['waive_withdrawal_right']

            try:
                # Process upgrade
                subscription = SubscriptionService.upgrade_to_paid(
                    craftsman=craftsman,
                    tier_name=tier_name,
                    payment_method_id=payment_method_id,
                    waive_withdrawal=waive_withdrawal
                )

                messages.success(
                    request,
                    f'Felicitări! Abonamentul tău {tier.display_name} este acum activ!'
                )
                return redirect('subscriptions:manage')

            except SubscriptionError as e:
                messages.error(request, f'Eroare la procesarea plății: {e}')
            except MissingFiscalDataError as e:
                messages.error(request, f'Date fiscale incomplete: {e}')
                return redirect('subscriptions:fiscal_data')
    else:
        form = UpgradeConfirmationForm()

    context = {
        'tier': tier,
        'form': form,
        'subscription': subscription,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY if hasattr(settings, 'STRIPE_PUBLISHABLE_KEY') else '',
    }

    return render(request, 'subscriptions/upgrade.html', context)


@login_required
def manage_subscription(request):
    """
    Manage current subscription - view details, cancel, update payment.
    """
    # Ensure user is a craftsman
    if not hasattr(request.user, 'craftsman_profile'):
        messages.error(request, 'Doar meseriașii pot gestiona abonamente.')
        return redirect('core:home')

    craftsman = request.user.craftsman_profile

    try:
        subscription = craftsman.subscription
    except CraftsmanSubscription.DoesNotExist:
        messages.error(request, 'Nu ai un abonament activ.')
        return redirect('subscriptions:pricing')

    # Get usage stats for Free tier
    usage_stats = None
    if subscription.tier.monthly_lead_limit is not None:
        usage_stats = {
            'used': subscription.leads_used_this_month,
            'limit': subscription.tier.monthly_lead_limit,
            'remaining': subscription.tier.monthly_lead_limit - subscription.leads_used_this_month,
            'percentage': int((subscription.leads_used_this_month / subscription.tier.monthly_lead_limit) * 100)
        }

    # Check if can request refund
    can_refund = subscription.can_request_refund() if hasattr(subscription, 'can_request_refund') else False

    context = {
        'subscription': subscription,
        'usage_stats': usage_stats,
        'can_refund': can_refund,
    }

    return render(request, 'subscriptions/manage.html', context)


@login_required
@require_POST
def cancel_subscription(request):
    """
    Cancel current subscription (downgrade to Free at period end).
    """
    # Ensure user is a craftsman
    if not hasattr(request.user, 'craftsman_profile'):
        return JsonResponse({'error': 'Only craftsmen can cancel subscriptions'}, status=403)

    craftsman = request.user.craftsman_profile

    try:
        subscription = craftsman.subscription
    except CraftsmanSubscription.DoesNotExist:
        return JsonResponse({'error': 'No active subscription'}, status=404)

    form = CancelSubscriptionForm(request.POST)
    if form.is_valid():
        try:
            # Cancel subscription
            SubscriptionService.cancel_subscription(craftsman)

            # Log cancellation reason if provided
            reason = form.cleaned_data.get('reason')
            feedback = form.cleaned_data.get('feedback')
            if reason or feedback:
                from .models import SubscriptionLog
                SubscriptionLog.objects.create(
                    subscription=subscription,
                    event_type='cancel',
                    old_tier=subscription.tier,
                    new_tier=subscription.tier,
                    metadata={
                        'reason': reason,
                        'feedback': feedback,
                    }
                )

            messages.success(
                request,
                'Abonamentul a fost anulat. Vei păstra accesul până la sfârșitul perioadei de facturare.'
            )
            return JsonResponse({'success': True, 'redirect': reverse('subscriptions:manage')})

        except SubscriptionError as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Invalid form data', 'errors': form.errors}, status=400)


@login_required
def request_refund(request):
    """
    Request refund within 14-day withdrawal period (OUG 34/2014).
    """
    # Ensure user is a craftsman
    if not hasattr(request.user, 'craftsman_profile'):
        messages.error(request, 'Doar meseriașii pot solicita rambursări.')
        return redirect('core:home')

    craftsman = request.user.craftsman_profile

    try:
        subscription = craftsman.subscription
    except CraftsmanSubscription.DoesNotExist:
        messages.error(request, 'Nu ai un abonament activ.')
        return redirect('subscriptions:pricing')

    # Check if can request refund
    if not (subscription.can_request_refund() if hasattr(subscription, 'can_request_refund') else False):
        messages.error(request, 'Nu poți solicita rambursare. Perioada de 14 zile a expirat.')
        return redirect('subscriptions:manage')

    if request.method == 'POST':
        form = RequestRefundForm(request.POST)
        if form.is_valid():
            try:
                # Process refund
                result = SubscriptionService.request_refund(craftsman)

                messages.success(
                    request,
                    f'Rambursarea de {result["amount_ron"]} RON a fost procesată! '
                    f'Banii vor ajunge în contul tău în 5-7 zile lucrătoare.'
                )
                return redirect('subscriptions:manage')

            except SubscriptionError as e:
                messages.error(request, f'Eroare la procesarea rambursării: {e}')
    else:
        form = RequestRefundForm()

    context = {
        'form': form,
        'subscription': subscription,
        'refund_amount': subscription.tier.price / 100,  # Convert cents to RON
    }

    return render(request, 'subscriptions/request_refund.html', context)


@login_required
def billing_portal(request):
    """
    Redirect to Stripe Customer Portal for self-service payment management.
    """
    # Ensure user is a craftsman
    if not hasattr(request.user, 'craftsman_profile'):
        messages.error(request, 'Doar meseriașii pot accesa portalul de facturare.')
        return redirect('core:home')

    craftsman = request.user.craftsman_profile

    try:
        subscription = craftsman.subscription
    except CraftsmanSubscription.DoesNotExist:
        messages.error(request, 'Nu ai un abonament activ.')
        return redirect('subscriptions:pricing')

    if not subscription.stripe_customer_id:
        messages.error(request, 'Nu ai un cont Stripe asociat.')
        return redirect('subscriptions:manage')

    try:
        # Create Stripe billing portal session
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=request.build_absolute_uri(reverse('subscriptions:manage'))
        )

        return redirect(session.url)

    except stripe.error.StripeError as e:
        messages.error(request, f'Eroare la accesarea portalului de facturare: {e}')
        return redirect('subscriptions:manage')
