from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Avg, Count
from django.db import transaction
from django.http import JsonResponse, Http404
from django.utils import timezone
from datetime import timedelta
from .models import ServiceCategory, Service, Order, Quote, Review, ReviewImage, Notification, notify_new_quote, notify_quote_accepted, notify_quote_rejected, Invitation, Shortlist, CreditWallet, WalletTransaction, CoverageArea, CraftsmanService
from .forms import OrderForm, ReviewForm, ReviewImageForm, MultipleReviewImageForm, QuoteForm, CraftsmanServiceForm
from accounts.models import CraftsmanProfile, County, City
from .decorators import CraftsmanRequiredMixin, ClientRequiredMixin, can_post_orders, can_post_services
from moderation.decorators import order_creation_limit, quote_creation_limit, review_creation_limit, RateLimitMixin


class ServiceCategoryListView(ListView):
    model = ServiceCategory
    template_name = 'services/category_list.html'
    context_object_name = 'categories'

    def dispatch(self, request, *args, **kwargs):
        # Return 404 for authenticated craftsmen trying to access categories page
        if request.user.is_authenticated and getattr(request.user, 'user_type', None) == 'craftsman':
            raise Http404("Pagina nu a fost găsită")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return ServiceCategory.objects.filter(is_active=True).annotate(
            orders_count=Count('services__order', filter=Q(services__order__status='published'))
        )


class ServiceCategoryDetailView(DetailView):
    model = ServiceCategory
    template_name = 'services/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = self.object.services.filter(is_active=True)
        context['recent_orders'] = Order.objects.filter(
            service__category=self.object,
            status='published'
        )[:6]

        # Add statistics for the category
        context['craftsmen_count'] = CraftsmanProfile.objects.filter(
            services__service__category=self.object
        ).distinct().count()

        context['completed_orders_count'] = Order.objects.filter(
            service__category=self.object,
            status='completed'
        ).count()

        context['featured_craftsmen'] = CraftsmanProfile.objects.filter(
            services__service__category=self.object,
            user__is_verified=True
        ).distinct()[:3]
        context['completed_orders'] = 150  # Placeholder
        return context


class CreateOrderView(ClientRequiredMixin, RateLimitMixin, CreateView):
    model = Order
    template_name = 'services/create_order.html'
    form_class = OrderForm

    # Rate limiting configuration
    rate_limit_type = 'order_creation'
    rate_limit_redirect_url = 'services:my_orders'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = ServiceCategory.objects.all().order_by('name')
        
        # Handle craftsman parameter for quote requests
        craftsman_id = self.request.GET.get('craftsman')
        if craftsman_id:
            try:
                craftsman = CraftsmanProfile.objects.get(pk=craftsman_id)
                context['craftsman'] = craftsman
                context['is_quote_request'] = True
                # Get services offered by this craftsman
                craftsman_services = craftsman.services.all().select_related('service__category')
                context['craftsman_services'] = craftsman_services
            except CraftsmanProfile.DoesNotExist:
                pass
        
        return context

    def form_valid(self, form):
        # Import the notification function
        from .models import notify_order_request
        
        form.instance.client = self.request.user
        
        # Handle craftsman parameter for direct quote requests
        craftsman_id = self.request.GET.get('craftsman')
        if craftsman_id:
            try:
                craftsman = CraftsmanProfile.objects.get(pk=craftsman_id)
                # Add a note to the order description that this is a direct request
                if form.instance.description:
                    form.instance.description += f"\n\n[Solicitare directă către meșterul {craftsman.user.get_full_name() or craftsman.user.username}]"
                else:
                    form.instance.description = f"[Solicitare directă către meșterul {craftsman.user.get_full_name() or craftsman.user.username}]"
            except CraftsmanProfile.DoesNotExist:
                pass
        
        response = super().form_valid(form)
        messages.success(self.request, 'Comanda a fost creată cu succes!')
        
        # If this was a direct craftsman request, notify the craftsman
        if craftsman_id:
            try:
                craftsman = CraftsmanProfile.objects.get(pk=craftsman_id)
                # Create notification for the craftsman
                notify_order_request(self.object, craftsman)
            except CraftsmanProfile.DoesNotExist:
                pass
        
        return response

    def get_success_url(self):
        return reverse_lazy('services:order_detail', kwargs={'pk': self.object.pk})


class OrderDetailView(DetailView):
    model = Order
    template_name = 'services/order_detail_simple.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()

        # Get all quotes for this order
        context['quotes'] = order.quotes.select_related('craftsman__user').order_by('-created_at')

        # Check if current user can quote (is craftsman and order is published)
        can_quote = False
        quote_disabled_reason = None

        if self.request.user.is_authenticated and self.request.user.user_type == 'craftsman':
            if order.status != 'published':
                quote_disabled_reason = 'Comanda nu este disponibilă pentru oferte'
            elif not hasattr(self.request.user, 'craftsman_profile'):
                quote_disabled_reason = 'Trebuie să îți completezi profilul de meșter'
            elif not self.request.user.craftsman_profile.can_bid_on_jobs():
                completion = self.request.user.craftsman_profile.profile_completion
                quote_disabled_reason = f'Profil incomplet ({completion}%) - completează profilul pentru a licita'
            elif order.quotes.filter(craftsman=self.request.user.craftsman_profile).exists():
                quote_disabled_reason = 'Ai trimis deja o ofertă pentru această comandă'
            else:
                can_quote = True

        context['can_quote'] = can_quote
        context['quote_disabled_reason'] = quote_disabled_reason

        return context


class EditOrderView(LoginRequiredMixin, UpdateView):
    model = Order
    template_name = 'services/edit_order.html'
    fields = [
        'title', 'description', 'service', 'county', 'city', 'address',
        'budget_min', 'budget_max', 'urgency', 'preferred_date'
    ]

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user)

    def get_success_url(self):
        return reverse_lazy('services:order_detail', kwargs={'pk': self.object.pk})


class MyOrdersView(ClientRequiredMixin, ListView):
    model = Order
    template_name = 'services/my_orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user).order_by('-created_at')


class MyQuotesView(CraftsmanRequiredMixin, ListView):
    model = Quote
    template_name = 'services/my_quotes.html'
    context_object_name = 'quotes'
    paginate_by = 10

    def get_queryset(self):
        return Quote.objects.filter(craftsman=self.request.user.craftsman_profile).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quotes = self.get_queryset()
        
        # Count quotes by status
        context['total_quotes'] = quotes.count()
        context['pending_quotes'] = quotes.filter(status='pending').count()
        context['accepted_quotes'] = quotes.filter(status='accepted').count()
        context['rejected_quotes'] = quotes.filter(status='rejected').count()
        context['declined_quotes'] = quotes.filter(status='declined').count()
        
        return context


class AvailableOrdersView(CraftsmanRequiredMixin, ListView):
    """View for craftsmen to see available orders they can quote on"""
    model = Order
    template_name = 'services/available_orders.html'
    context_object_name = 'orders'
    paginate_by = 12

    def get_queryset(self):
        craftsman = self.request.user.craftsman_profile
        
        # Limit to services registered by the craftsman
        service_ids = CraftsmanService.objects.filter(
            craftsman=craftsman
        ).values_list('service_id', flat=True)

        # Get published orders that the craftsman hasn't quoted on yet and match their services
        queryset = Order.objects.filter(
            status='published',
            service_id__in=service_ids
        ).exclude(
            quotes__craftsman=craftsman
        ).select_related('client', 'service').order_by('-created_at')
        
        # Filter by service category if requested
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(service__category__slug=category)
        
        # Filter by county if requested
        county = self.request.GET.get('county')
        if county:
            queryset = queryset.filter(county=county)
        
        return queryset.distinct()


class CreateQuoteView(LoginRequiredMixin, RateLimitMixin, CreateView):
    model = Quote
    template_name = 'services/create_quote.html'
    fields = ['price', 'description', 'estimated_duration']

    # Rate limiting configuration
    rate_limit_type = 'quote_creation'

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['order_pk'])

        # Check if user is craftsman and order is published
        if request.user.user_type != 'craftsman':
            messages.error(request, 'Doar meșterii pot trimite oferte.')
            return redirect('services:order_detail', pk=self.order.pk)

        if self.order.status != 'published':
            messages.error(request, 'Nu poți trimite oferte pentru această comandă.')
            return redirect('services:order_detail', pk=self.order.pk)

        # Check if craftsman has complete profile (GATING)
        if not hasattr(request.user, 'craftsman_profile'):
            messages.error(request, 'Trebuie să îți completezi profilul de meșter mai întâi.')
            return redirect('accounts:edit_craftsman_profile')

        craftsman_profile = request.user.craftsman_profile
        if not craftsman_profile.can_bid_on_jobs():
            missing_items = []
            if not craftsman_profile.profile_photo:
                missing_items.append('poză de profil')
            if craftsman_profile.portfolio_images.count() < 3:
                missing_items.append(f'{3 - craftsman_profile.portfolio_images.count()} poze portofoliu')
            if not craftsman_profile.bio or len(craftsman_profile.bio.strip()) < 200:
                missing_items.append('descriere completă (min. 200 caractere)')

            messages.error(request, 'Profilul tău nu este complet: ' + ', '.join(missing_items))
            return redirect('accounts:edit_craftsman_profile')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        return context

    def form_valid(self, form):
        form.instance.craftsman = self.request.user.craftsman_profile
        form.instance.order = self.order

        # Additional validation: Prevent duplicate quotes
        if Quote.objects.filter(order=self.order, craftsman=self.request.user.craftsman_profile).exists():
            messages.error(self.request, 'Ai trimis deja o ofertă pentru această comandă.')
            return redirect('services:order_detail', pk=self.order.pk)

        response = super().form_valid(form)
        messages.success(self.request, 'Oferta a fost trimisă cu succes!')

        # Create notification for client
        notify_new_quote(self.order, form.instance)

        return response

    def get_success_url(self):
        return reverse_lazy('services:order_detail', kwargs={'pk': self.order.pk})


class PublishOrderView(LoginRequiredMixin, DetailView):
    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        # Check if user is the owner
        if order.client != request.user:
            messages.error(request, 'Nu poți publica această comandă.')
            return redirect('services:order_detail', pk=order.pk)

        order.status = 'published'
        order.published_at = timezone.now()
        order.save()

        messages.success(request, 'Comanda a fost publicată și este acum disponibilă pentru oferte!')
        return redirect('services:order_detail', pk=order.pk)


class AcceptQuoteView(LoginRequiredMixin, DetailView):
    model = Quote

    def post(self, request, *args, **kwargs):
        quote = self.get_object()

        # Check if user is the order owner
        if quote.order.client != request.user:
            messages.error(request, 'Nu poți accepta această ofertă.')
            return redirect('services:order_detail', pk=quote.order.pk)

        # Mark this quote as accepted and the rest as rejected
        quote.status = 'accepted'
        quote.save()

        # Assign the craftsman to the order and update status
        order = quote.order
        order.assigned_craftsman = quote.craftsman
        order.status = 'awaiting_confirmation'
        order.selected_at = timezone.now()
        order.save()

        # Notify the craftsman
        notify_quote_accepted(quote)

        messages.success(request, 'Oferta a fost acceptată! Așteptăm confirmarea meșterului.')
        return redirect('services:order_detail', pk=order.pk)


class RejectQuoteView(LoginRequiredMixin, DetailView):
    model = Quote

    def post(self, request, *args, **kwargs):
        quote = self.get_object()

        # Check if user is the order owner
        if quote.order.client != request.user:
            messages.error(request, 'Nu poți respinge această ofertă.')
            return redirect('services:order_detail', pk=quote.order.pk)

        # Mark this quote as rejected
        quote.status = 'rejected'
        quote.save()

        # Notify the craftsman
        notify_quote_rejected(quote)

        messages.success(request, 'Oferta a fost respinsă.')
        return redirect('services:order_detail', pk=quote.order.pk)


class ConfirmOrderView(LoginRequiredMixin, DetailView):
    """View for craftsmen to confirm they will take on an order"""
    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        # Check if user is the assigned craftsman
        if (not hasattr(request.user, 'craftsman_profile') or
            order.assigned_craftsman != request.user.craftsman_profile):
            messages.error(request, 'Nu poți confirma această comandă.')
            return redirect('services:order_detail', pk=order.pk)

        # Check if order is awaiting confirmation
        if order.status != 'awaiting_confirmation':
            messages.error(request, 'Această comandă nu poate fi confirmată.')
            return redirect('services:order_detail', pk=order.pk)

        # Confirm the order
        order.status = 'in_progress'
        order.confirmed_at = timezone.now()
        order.save()

        # Create notification for client
        Notification.objects.create(
            recipient=order.client,
            notification_type='order_confirmed',
            title=f'Meșterul a confirmat comanda!',
            message=f'Meșterul {order.assigned_craftsman.user.get_full_name() or order.assigned_craftsman.user.username} a confirmat că va prelua comanda "{order.title}". Lucrarea poate începe.',
            order=order
        )

        messages.success(request, 'Ai confirmat preluarea comenzii! Clientul va fi notificat.')
        return redirect('services:order_detail', pk=order.pk)


class DeclineOrderView(LoginRequiredMixin, DetailView):
    """View for craftsmen to decline an order after being selected"""
    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        # Check if user is the assigned craftsman
        if (not hasattr(request.user, 'craftsman_profile') or
            order.assigned_craftsman != request.user.craftsman_profile):
            messages.error(request, 'Nu poți refuza această comandă.')
            return redirect('services:order_detail', pk=order.pk)

        # Check if order is awaiting confirmation
        if order.status != 'awaiting_confirmation':
            messages.error(request, 'Această comandă nu poate fi refuzată.')
            return redirect('services:order_detail', pk=order.pk)

        # Decline the order - reset to published status
        order.status = 'published'
        order.assigned_craftsman = None
        order.selected_at = None
        order.save()

        # Reset the accepted quote back to pending
        accepted_quote = Quote.objects.filter(order=order, status='accepted').first()
        if accepted_quote:
            accepted_quote.status = 'declined'
            accepted_quote.save()

        # Create notification for client
        Notification.objects.create(
            recipient=order.client,
            notification_type='order_declined',
            title=f'Meșterul a refuzat comanda',
            message=f'Din păcate, meșterul {request.user.get_full_name() or request.user.username} nu poate prelua comanda "{order.title}". Comanda a fost republicată pentru alte oferte.',
            order=order
        )

        messages.success(request, 'Ai refuzat comanda. Clientul va fi notificat și comanda va fi republicată.')
        return redirect('services:available_orders')


class CreateReviewView(LoginRequiredMixin, CreateView):
    """Enhanced review creation with image upload support"""
    model = Review
    form_class = ReviewForm
    template_name = 'services/create_review.html'

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['pk'])

        # Check if user can review this order
        if self.order.client != request.user:
            messages.error(request, 'Nu poți lăsa o recenzie pentru această comandă.')
            return redirect('services:order_detail', pk=self.order.pk)

        # Check if review already exists
        if hasattr(self.order, 'review'):
            messages.info(request, 'Ai lăsat deja o recenzie pentru această comandă.')
            return redirect('services:order_detail', pk=self.order.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        context['image_form'] = MultipleReviewImageForm()
        return context

    def form_valid(self, form):
        form.instance.order = self.order
        form.instance.client = self.request.user
        form.instance.craftsman = self.order.assigned_craftsman

        response = super().form_valid(form)

        # Handle image uploads
        image_form = MultipleReviewImageForm(self.request.POST, self.request.FILES)
        if image_form.is_valid():
            images = image_form.get_images()
            for i, image in enumerate(images):
                ReviewImage.objects.create(
                    review=self.object,
                    image=image,
                    description=f'Imagine {i + 1}'
                )

        # Update craftsman ratings
        self._update_craftsman_ratings()

        # Update order status
        self.order.status = 'completed'
        self.order.save()

        messages.success(self.request, 'Recenzia a fost adăugată cu succes!')
        return response

    def _update_craftsman_ratings(self):
        """Update craftsman's average rating and review count"""
        craftsman = self.order.assigned_craftsman
        reviews = Review.objects.filter(craftsman=craftsman)

        # Calculate new averages
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        total_reviews = reviews.count()

        # Update craftsman profile
        craftsman.average_rating = round(avg_rating, 2)
        craftsman.total_reviews = total_reviews
        craftsman.save()

    def get_success_url(self):
        return reverse_lazy('services:order_detail', kwargs={'pk': self.order.pk})


class ReviewDetailView(DetailView):
    """View for displaying individual review details"""
    model = Review
    template_name = 'services/review_detail.html'
    context_object_name = 'review'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review_images'] = self.object.images.all()
        return context


class CraftsmanReviewsView(ListView):
    """View for displaying all reviews for a craftsman"""
    model = Review
    template_name = 'services/craftsman_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.craftsman = get_object_or_404(CraftsmanProfile, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Review.objects.filter(craftsman=self.craftsman).select_related(
            'client', 'order'
        ).prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['craftsman'] = self.craftsman

        # Calculate review statistics
        reviews = self.get_queryset()
        context['total_reviews'] = reviews.count()
        context['average_rating'] = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

        # Rating distribution
        rating_counts = {}
        for i in range(1, 6):
            rating_counts[i] = reviews.filter(rating=i).count()
        context['rating_distribution'] = rating_counts

        return context


class ReviewImageUploadView(LoginRequiredMixin, CreateView):
    """View for uploading additional review images"""
    model = ReviewImage
    form_class = ReviewImageForm
    template_name = 'services/upload_review_image.html'

    def dispatch(self, request, *args, **kwargs):
        self.review = get_object_or_404(Review, pk=kwargs['review_pk'])

        # Check if user owns this review
        if self.review.client != request.user:
            messages.error(request, 'Nu poți adăuga imagini la această recenzie.')
            return redirect('services:review_detail', pk=self.review.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.review = self.review
        messages.success(self.request, 'Imaginea a fost adăugată la recenzie.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('services:review_detail', kwargs={'pk': self.review.pk})


class MyOrdersView(LoginRequiredMixin, ListView):
    """View for user's orders"""
    model = Order
    template_name = 'services/my_orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user).order_by('-created_at')


LEAD_FEE_CENTS = 2000  # 20 lei exemplu


class InviteCraftsmenView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'services/invite_craftsmen.html'
    context_object_name = 'order'

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()

        # Only the owner can invite craftsmen
        if order.client != request.user:
            messages.error(request, 'Nu poți invita meșteri pentru această comandă.')
            return redirect('services:order_detail', pk=order.pk)

        # Check if order is published
        if order.status != 'published':
            messages.error(request, 'Comanda trebuie să fie publicată pentru a invita meșteri.')
            return redirect('services:order_detail', pk=order.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()

        # Get craftsmen in the same category and area
        craftsmen = CraftsmanProfile.objects.filter(
            services__service__category=order.service.category,
            user__user_type='craftsman'
        ).select_related('user', 'county', 'city').distinct()

        # Filter by location if coverage area exists
        # TODO: Implement distance-based filtering

        # Exclude already invited craftsmen
        invited_craftsmen_ids = order.invitations.values_list('craftsman_id', flat=True)
        craftsmen = craftsmen.exclude(user_id__in=invited_craftsmen_ids)

        # Exclude craftsmen who already quoted
        quoted_craftsmen_ids = order.quotes.values_list('craftsman__user_id', flat=True)
        craftsmen = craftsmen.exclude(user_id__in=quoted_craftsmen_ids)

        context['craftsmen'] = craftsmen[:20]  # Limit to 20 for performance
        context['invited_count'] = order.invitations.count()

        return context

    def post(self, request, *args, **kwargs):
        """Handle craftsman invitations"""
        order = self.get_object()
        craftsman_ids = request.POST.getlist('craftsman_ids')

        invited_count = 0
        for craftsman_id in craftsman_ids:
            try:
                craftsman = get_object_or_404(CraftsmanProfile, user_id=craftsman_id)
                invitation, created = Invitation.objects.get_or_create(
                    order=order,
                    craftsman=craftsman.user,
                    defaults={'invited_by': request.user}
                )
                if created:
                    invited_count += 1
                    # TODO: Send notification to craftsman
            except:
                continue

        if invited_count > 0:
            messages.success(request, f'Au fost invitați {invited_count} meșteri să oferteze.')
        else:
            messages.info(request, 'Nu au fost invitați meșteri noi.')

        return redirect('services:order_detail', pk=order.pk)


class ShortlistCraftsmanView(LoginRequiredMixin, DetailView):
    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        # Only the order owner can shortlist craftsmen
        if order.client != request.user:
            messages.error(request, 'Nu poți adăuga meșteri pe lista scurtă pentru această comandă.')
            return redirect('services:order_detail', pk=order.pk)

        craftsman_id = request.POST.get('craftsman_id')
        craftsman = get_object_or_404(CraftsmanProfile, pk=craftsman_id)

        # Create or update shortlist
        shortlist, created = Shortlist.objects.get_or_create(order=order)
        shortlist.craftsmen.add(craftsman)

        messages.success(request, 'Meșterul a fost adăugat pe lista scurtă!')
        return redirect('services:invite_craftsmen', pk=order.pk)


class WalletView(LoginRequiredMixin, DetailView):
    model = CreditWallet
    template_name = 'services/wallet.html'

    def dispatch(self, request, *args, **kwargs):
        # Ensure the user has a wallet
        if not hasattr(request.user, 'creditwallet'):
            CreditWallet.objects.create(user=request.user, balance=0)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user.creditwallet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = WalletTransaction.objects.filter(wallet=self.object).order_by('-created_at')
        return context


# Craftsman Services Management Views

class CraftsmanServicesView(CraftsmanRequiredMixin, ListView):
    """View for craftsmen to manage their services"""
    model = CraftsmanService
    template_name = 'services/craftsman_services.html'
    context_object_name = 'services'
    paginate_by = 20

    def get_queryset(self):
        return CraftsmanService.objects.filter(
            craftsman=self.request.user.craftsman_profile
        ).select_related('service__category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['craftsman'] = self.request.user.craftsman_profile
        context['total_services'] = self.get_queryset().count()
        return context


class AddCraftsmanServiceView(CraftsmanRequiredMixin, CreateView):
    """View for craftsmen to add new services"""
    model = CraftsmanService
    form_class = CraftsmanServiceForm
    template_name = 'services/add_craftsman_service.html'

    def form_valid(self, form):
        form.instance.craftsman = self.request.user.craftsman_profile

        # Check if service already exists for this craftsman
        if CraftsmanService.objects.filter(
            craftsman=self.request.user.craftsman_profile,
            service=form.cleaned_data['service']
        ).exists():
            messages.error(self.request, 'Ai adăugat deja acest serviciu.')
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, 'Serviciul a fost adăugat cu succes!')
        return response

    def get_success_url(self):
        return reverse_lazy('services:craftsman_services')


class EditCraftsmanServiceView(CraftsmanRequiredMixin, UpdateView):
    """View for craftsmen to edit their services"""
    model = CraftsmanService
    form_class = CraftsmanServiceForm
    template_name = 'services/edit_craftsman_service.html'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        # If the parent dispatch returned a redirect, return it
        if hasattr(response, 'status_code') and response.status_code == 302:
            return response

        service = self.get_object()

        # Only allow the owner to edit
        if service.craftsman.user != request.user:
            messages.error(request, 'Nu poți edita acest serviciu.')
            return redirect('services:craftsman_services')

        return response

    def get_queryset(self):
        return CraftsmanService.objects.filter(
            craftsman=self.request.user.craftsman_profile
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Serviciul a fost actualizat cu succes!')
        return response

    def get_success_url(self):
        return reverse_lazy('services:craftsman_services')


class DeleteCraftsmanServiceView(CraftsmanRequiredMixin, DetailView):
    """View for craftsmen to delete their services"""
    model = CraftsmanService

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        # If the parent dispatch returned a redirect, return it
        if hasattr(response, 'status_code') and response.status_code == 302:
            return response

        service = self.get_object()

        # Only allow the owner to delete
        if service.craftsman.user != request.user:
            messages.error(request, 'Nu poți șterge acest serviciu.')
            return redirect('services:craftsman_services')

        return response

    def post(self, request, *args, **kwargs):
        service = self.get_object()
        service_name = service.service.name
        service.delete()

        messages.success(request, f'Serviciul "{service_name}" a fost șters cu succes!')
        return redirect('services:craftsman_services')

    def get_queryset(self):
        return CraftsmanService.objects.filter(
            craftsman=self.request.user.craftsman_profile
        )


class NotificationsView(LoginRequiredMixin, ListView):
    """View for displaying user notifications"""
    model = Notification
    template_name = 'services/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Count unread notifications
        unread_count = Notification.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        
        context['unread_count'] = unread_count
        return context

    def get(self, request, *args, **kwargs):
        # Mark all notifications as read when viewing the page
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return super().get(request, *args, **kwargs)
