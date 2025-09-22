from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import ServiceCategory, Service, Order, Quote, Review, ReviewImage, Notification, notify_new_quote, notify_quote_accepted, notify_quote_rejected
from .forms import OrderForm, ReviewForm, ReviewImageForm, MultipleReviewImageForm, QuoteForm
from accounts.models import CraftsmanProfile, County, City


class ServiceCategoryListView(ListView):
    model = ServiceCategory
    template_name = 'services/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return ServiceCategory.objects.filter(is_active=True)


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
        # Add craftsmen count and featured craftsmen
        context['craftsmen_count'] = CraftsmanProfile.objects.filter(
            services__service__category=self.object
        ).distinct().count()
        context['featured_craftsmen'] = CraftsmanProfile.objects.filter(
            services__service__category=self.object,
            user__is_verified=True
        ).distinct()[:3]
        context['completed_orders'] = 150  # Placeholder
        return context


class CreateOrderView(CreateView):
    model = Order
    template_name = 'services/create_order.html'
    form_class = OrderForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = ServiceCategory.objects.all().order_by('name')
        return context

    def form_valid(self, form):
        form.instance.client = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Comanda a fost creată cu succes!')
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
        context['can_quote'] = (
            self.request.user.is_authenticated and
            self.request.user.user_type == 'craftsman' and
            order.status == 'published' and
            not order.quotes.filter(craftsman=self.request.user.craftsman_profile).exists()
        )

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


class MyOrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'services/my_orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user).order_by('-created_at')


class CreateQuoteView(LoginRequiredMixin, CreateView):
    model = Quote
    template_name = 'services/create_quote.html'
    fields = ['price', 'description', 'estimated_duration']

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs['order_pk'])

        # Check if user is craftsman and order is published
        if request.user.user_type != 'craftsman':
            messages.error(request, 'Doar meșterii pot trimite oferte.')
            return redirect('services:order_detail', pk=self.order.pk)

        if self.order.status != 'published':
            messages.error(request, 'Nu poți trimite oferte pentru această comandă.')
            return redirect('services:order_detail', pk=self.order.pk)

        # Check if craftsman already has a quote for this order
        if Quote.objects.filter(order=self.order, craftsman=request.user.craftsman_profile).exists():
            messages.error(request, 'Ai trimis deja o ofertă pentru această comandă.')
            return redirect('services:order_detail', pk=self.order.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        return context

    def form_valid(self, form):
        form.instance.order = self.order
        form.instance.craftsman = self.request.user.craftsman_profile
        # Set expiration date to 7 days from now
        form.instance.expires_at = timezone.now() + timedelta(days=7)
        response = super().form_valid(form)

        # Send notification to client
        notify_new_quote(form.instance)

        messages.success(self.request, 'Oferta a fost trimisă cu succes!')
        return response

    def get_success_url(self):
        return reverse_lazy('services:order_detail', kwargs={'pk': self.order.pk})


class PublishOrderView(LoginRequiredMixin, DetailView):
    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        # Check if user owns the order
        if order.client != request.user:
            messages.error(request, 'Nu poți publica această comandă.')
            return redirect('services:order_detail', pk=order.pk)

        # Check if order is in draft status
        if order.status != 'draft':
            messages.error(request, 'Această comandă a fost deja publicată.')
            return redirect('services:order_detail', pk=order.pk)

        # Publish the order
        order.status = 'published'
        order.published_at = timezone.now()
        order.save()

        messages.success(request, 'Comanda a fost publicată cu succes! Meșterii vor putea trimite oferte.')
        return redirect('services:order_detail', pk=order.pk)


class AcceptQuoteView(LoginRequiredMixin, DetailView):
    model = Quote

    def post(self, request, *args, **kwargs):
        quote = self.get_object()
        if quote.order.client == request.user and quote.status == 'pending':
            quote.status = 'accepted'
            quote.save()

            # Update order status and assign craftsman
            quote.order.status = 'in_progress'
            quote.order.assigned_craftsman = quote.craftsman
            quote.order.save()

            # Reject all other quotes for this order and notify craftsmen
            rejected_quotes = Quote.objects.filter(order=quote.order).exclude(pk=quote.pk)
            for rejected_quote in rejected_quotes:
                rejected_quote.status = 'rejected'
                rejected_quote.save()
                notify_quote_rejected(rejected_quote)

            # Notify the accepted craftsman
            notify_quote_accepted(quote)

            messages.success(request, 'Oferta a fost acceptată! Meșterul va fi notificat.')
        else:
            messages.error(request, 'Nu poți accepta această ofertă.')

        return redirect('services:order_detail', pk=quote.order.pk)


class RejectQuoteView(LoginRequiredMixin, DetailView):
    model = Quote

    def post(self, request, *args, **kwargs):
        quote = self.get_object()
        if quote.order.client == request.user and quote.status == 'pending':
            quote.status = 'rejected'
            quote.save()

            # Notify craftsman about rejection
            notify_quote_rejected(quote)

            messages.success(request, 'Oferta a fost respinsă.')
        else:
            messages.error(request, 'Nu poți respinge această ofertă.')

        return redirect('services:order_detail', pk=quote.order.pk)


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


class AvailableOrdersView(LoginRequiredMixin, ListView):
    """View for craftsmen to see available orders"""
    model = Order
    template_name = 'services/available_orders.html'
    context_object_name = 'orders'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        # Only allow craftsmen to access this view
        if not hasattr(request.user, 'craftsmanprofile'):
            messages.error(request, 'Doar meșterii pot accesa această pagină.')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Order.objects.filter(status='published').order_by('-created_at')

        # Filter by search query
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(service__category__name__icontains=search_query)
            )

        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(service__category_id=category_id)

        # Filter by county
        county_id = self.request.GET.get('county')
        if county_id:
            queryset = queryset.filter(county_id=county_id)

        # Filter by city
        city_id = self.request.GET.get('city')
        if city_id:
            queryset = queryset.filter(city_id=city_id)

        # Filter by urgency
        urgency = self.request.GET.get('urgency')
        if urgency:
            queryset = queryset.filter(urgency=urgency)

        # Filter by budget range
        min_budget = self.request.GET.get('min_budget')
        max_budget = self.request.GET.get('max_budget')
        if min_budget:
            queryset = queryset.filter(budget_min__gte=min_budget)
        if max_budget:
            queryset = queryset.filter(budget_max__lte=max_budget)

        return queryset.select_related('service__category', 'county', 'city', 'client')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ServiceCategory.objects.filter(is_active=True).order_by('name')
        context['counties'] = County.objects.all().order_by('name')

        # Add current filter values to context
        context['current_filters'] = {
            'q': self.request.GET.get('q', ''),
            'category': self.request.GET.get('category', ''),
            'county': self.request.GET.get('county', ''),
            'city': self.request.GET.get('city', ''),
            'urgency': self.request.GET.get('urgency', ''),
            'min_budget': self.request.GET.get('min_budget', ''),
            'max_budget': self.request.GET.get('max_budget', ''),
        }

        # Add cities for selected county
        county_id = self.request.GET.get('county')
        if county_id:
            context['cities'] = City.objects.filter(county_id=county_id).order_by('name')
        else:
            context['cities'] = []

        # Add statistics
        context['total_orders'] = self.get_queryset().count()
        context['urgency_choices'] = Order.URGENCY_CHOICES

        return context
