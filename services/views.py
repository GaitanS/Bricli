import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

logger = logging.getLogger(__name__)
from accounts.models import County, CraftsmanProfile
from notifications.models import Notification

# RateLimitMixin ELIMINAT - nu mai este necesar
from notifications.services import NotificationService

from .decorators import ClientRequiredMixin, CraftsmanRequiredMixin
from .forms import CraftsmanServiceForm, MultipleReviewImageForm, OrderForm, ReviewForm, ReviewImageForm
from .models import (
    CraftsmanService,
    CreditWallet,
    Invitation,
    Order,
    OrderImage,
    Quote,
    Review,
    ReviewImage,
    ServiceCategory,
    Shortlist,
    WalletTransaction,
)
from .querydefs import q_active, q_completed, q_public_orders, q_active_craftsmen


class ServiceCategoryListView(ListView):
    model = ServiceCategory
    template_name = "services/category_list.html"
    context_object_name = "categories"

    def dispatch(self, request, *args, **kwargs):
        # Return 404 for authenticated craftsmen trying to access categories page
        if request.user.is_authenticated and getattr(request.user, "user_type", None) == "craftsman":
            raise Http404("Pagina nu a fost găsită")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        from django.core.cache import cache

        from core.cache_utils import CacheManager

        cache_key = CacheManager.generate_key("service_categories_with_stats")

        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        queryset = (
            ServiceCategory.objects.filter(is_active=True)
            .annotate(orders_count=Count("services__order", filter=Q(services__order__status="published")))
            .order_by("name")  # Alphabetical ordering
        )

        # Cache the result for 30 minutes
        cache.set(cache_key, queryset, 1800)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories_count"] = self.get_queryset().count()
        context["craftsmen_count"] = CraftsmanProfile.objects.filter(
            user__is_active=True, is_active=True
        ).count()
        return context


class ServiceCategoryDetailView(DetailView):
    model = ServiceCategory
    template_name = "services/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        # Services in this category
        context["services"] = category.services.filter(is_active=True)
        context["popular_services"] = category.services.filter(is_active=True, is_popular=True).order_by("name")[:100]

        # Public orders in this category (show more orders - 12 instead of 6)
        context["recent_orders"] = (
            Order.objects
            .filter(q_public_orders())  # Use helper: public orders only
            .filter(service__category=category)
            .select_related('client', 'service', 'county', 'city')
            .order_by('-created_at')[:12]
        )

        # Craftsmen statistics (use correct relationship path)
        context["craftsmen_count"] = (
            CraftsmanProfile.objects
            .filter(services__service__category=category)
            .distinct()
            .count()
        )

        # Completed orders count
        context["completed_orders_count"] = Order.objects.filter(
            service__category=category,
            status="completed"
        ).count()

        # Featured craftsmen - use permissive filter (removed is_verified requirement)
        context["featured_craftsmen"] = (
            CraftsmanProfile.objects
            .filter(q_active_craftsmen())  # Use helper: active craftsmen
            .filter(services__service__category=category)
            .distinct()
            .select_related('user', 'county', 'city')
            .annotate(
                rating_avg=Avg('received_reviews__rating'),
                reviews_count=Count('received_reviews')
            )[:12]  # Show more craftsmen - 12 instead of 3
        )

        return context


class CreateOrderView(ClientRequiredMixin, CreateView):
    model = Order
    template_name = "services/create_order.html"
    form_class = OrderForm

    # Rate limiting ELIMINAT - nu mai sunt restricții

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["services"] = ServiceCategory.objects.all().order_by("name")

        # Handle craftsman parameter for quote requests
        craftsman_id = self.request.GET.get("craftsman")
        if craftsman_id:
            try:
                craftsman = CraftsmanProfile.objects.get(pk=craftsman_id)
                context["craftsman"] = craftsman
                context["is_quote_request"] = True
                # Get services offered by this craftsman
                craftsman_services = craftsman.services.all().select_related("service__category")
                context["craftsman_services"] = craftsman_services
            except CraftsmanProfile.DoesNotExist:
                pass

        return context

    def form_valid(self, form):
        # Import the notification function
        from .models import notify_order_request

        form.instance.client = self.request.user

        # Handle craftsman parameter for direct quote requests
        craftsman_id = self.request.GET.get("craftsman")
        craftsman = None
        if craftsman_id:
            try:
                craftsman = CraftsmanProfile.objects.get(pk=craftsman_id)
                # Set assigned_craftsman to mark this as a direct request
                form.instance.assigned_craftsman = craftsman
            except CraftsmanProfile.DoesNotExist:
                pass

        response = super().form_valid(form)

        # Handle image uploads
        images = self.request.FILES.getlist("images")
        for image in images:
            OrderImage.objects.create(order=self.object, image=image)

        messages.success(self.request, "Comanda a fost creată cu succes!")

        # If this was a direct craftsman request, notify the craftsman
        if craftsman_id:
            try:
                craftsman = CraftsmanProfile.objects.get(pk=craftsman_id)
                # Create notification for the craftsman
                notify_order_request(self.object, craftsman)
                # Create an invitation record so the craftsman can accept/decline
                Invitation.objects.get_or_create(
                    order=self.object, craftsman=craftsman.user, defaults={"invited_by": self.request.user}
                )
            except CraftsmanProfile.DoesNotExist:
                pass

        return response

    def get_success_url(self):
        return reverse_lazy("services:order_detail", kwargs={"pk": self.object.pk})


class OrderDetailView(DetailView):
    model = Order
    template_name = "services/order_detail_simple.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related(
            "client", "service", "service__category", "county", "city", "assigned_craftsman__user"
        ).prefetch_related("images", "quotes__craftsman__user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()

        # Get all quotes for this order
        context["quotes"] = order.quotes.select_related("craftsman__user").order_by("-created_at")

        # Add filtered order counters for client dashboard
        context["active_orders_count"] = order.client.orders.filter(q_active()).count()
        context["completed_orders_count"] = order.client.orders.filter(q_completed()).count()

        # Invitație existentă pentru meșterul curent (calculată înainte de verificări)
        invitation = None
        if self.request.user.is_authenticated and getattr(self.request.user, "user_type", None) == "craftsman":
            invitation = Invitation.objects.filter(order=order, craftsman=self.request.user).first()
        context["invitation"] = invitation

        # Check if current user can quote (is craftsman and order is published OR invitație acceptată)
        can_quote = False
        quote_disabled_reason = None

        if self.request.user.is_authenticated and self.request.user.user_type == "craftsman":
            invited_and_accepted = invitation and invitation.status == "accepted"
            if order.status != "published" and not invited_and_accepted:
                if invitation and invitation.status == "pending":
                    quote_disabled_reason = (
                        "Ai o invitație pentru această lucrare. Acceptă invitația pentru a trimite ofertă"
                    )
                else:
                    quote_disabled_reason = "Comanda nu este disponibilă pentru oferte"
            elif not hasattr(self.request.user, "craftsman_profile"):
                quote_disabled_reason = "Trebuie să îți completezi profilul de meșter"
            elif not self.request.user.craftsman_profile.can_bid_on_jobs():
                completion = self.request.user.craftsman_profile.profile_completion
                quote_disabled_reason = f"Profil incomplet ({completion}%) - completează profilul pentru a licita"
            elif order.quotes.filter(craftsman=self.request.user.craftsman_profile).exists():
                quote_disabled_reason = "Ai trimis deja o ofertă pentru această comandă"
            else:
                can_quote = True

        context["can_quote"] = can_quote
        context["quote_disabled_reason"] = quote_disabled_reason

        return context


class EditOrderView(LoginRequiredMixin, UpdateView):
    model = Order
    template_name = "services/edit_order.html"
    fields = [
        "title",
        "description",
        "service",
        "county",
        "city",
        "address",
        "budget_min",
        "budget_max",
        "urgency",
        "preferred_date",
    ]

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user)

    def get_success_url(self):
        return reverse_lazy("services:order_detail", kwargs={"pk": self.object.pk})


class MyOrdersView(ClientRequiredMixin, ListView):
    model = Order
    template_name = "services/my_orders.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        from django.db.models import Prefetch

        qs = (
            Order.objects.filter(client=self.request.user)
            .select_related("service", "service__category", "county", "city")
            .prefetch_related("quotes")
        )

        # Safely prefetch reviews - Order has OneToOne with Review (related_name="review")
        try:
            from services.models import Review

            # For OneToOne, just select_related is enough (no prefetch needed)
            qs = qs.select_related("review")
        except Exception:
            pass

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filtered counters for order status tabs
        user_orders = Order.objects.filter(client=self.request.user)
        context["total_orders_count"] = user_orders.count()
        context["active_orders_count"] = user_orders.filter(q_active()).count()
        context["completed_orders_count"] = user_orders.filter(q_completed()).count()
        context["pending_orders_count"] = user_orders.filter(status="published").count()

        return context


class MyQuotesView(CraftsmanRequiredMixin, ListView):
    model = Quote
    template_name = "services/my_quotes.html"
    context_object_name = "quotes"
    paginate_by = 10

    def get_queryset(self):
        return (
            Quote.objects.filter(craftsman=self.request.user.craftsman_profile)
            .select_related("order", "order__client", "order__service", "order__service__category")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quotes = self.get_queryset()

        # Count quotes by status
        context["total_quotes"] = quotes.count()
        context["pending_quotes"] = quotes.filter(status="pending").count()
        context["accepted_quotes"] = quotes.filter(status="accepted").count()
        context["rejected_quotes"] = quotes.filter(status="rejected").count()
        context["declined_quotes"] = quotes.filter(status="declined").count()

        return context


class AvailableOrdersView(CraftsmanRequiredMixin, ListView):
    """View for craftsmen to see available orders they can quote on"""

    model = Order
    template_name = "services/available_orders.html"
    context_object_name = "orders"
    paginate_by = 12

    def get_paginate_by(self, queryset):
        """Allow dynamic page size based on user preference"""
        page_size = self.request.GET.get("page_size")
        if page_size and page_size.isdigit():
            page_size = int(page_size)
            # Limit page size to reasonable values
            if 1 <= page_size <= 100:
                return page_size
        return self.paginate_by

    def get_queryset(self):
        from django.core.cache import cache

        from core.cache_utils import CacheManager

        craftsman = self.request.user.craftsman_profile

        # Create cache key based on craftsman, filters, and page size
        category = self.request.GET.get("category", "")
        county = self.request.GET.get("county", "")
        page_size = self.get_paginate_by(None)

        cache_key = CacheManager.generate_key(
            "available_orders", craftsman_id=craftsman.id, category=category, county=county, page_size=page_size
        )

        # Try to get from cache first (shorter cache time for orders)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Limit to services registered by the craftsman
        service_ids = CraftsmanService.objects.filter(craftsman=craftsman).values_list("service_id", flat=True)

        # Get published orders that the craftsman hasn't quoted on yet and match their services
        # EXCLUDE direct requests (orders with assigned_craftsman) from available orders listing
        queryset = (
            Order.objects.filter(status="published", service_id__in=service_ids)
            .exclude(quotes__craftsman=craftsman)
            .exclude(assigned_craftsman__isnull=False)  # Hide direct requests
            .select_related("client", "service", "service__category", "county", "city")
            .prefetch_related("quotes", "invitations")
            .order_by("-created_at")
        )
        # Include invited orders even if not published? We keep only published here for listing

        # Filter by service category if requested
        if category:
            queryset = queryset.filter(service__category__slug=category)

        # Filter by county if requested
        if county:
            queryset = queryset.filter(county=county)

        queryset = queryset.distinct()

        # Cache the result for 5 minutes (orders change frequently)
        cache.set(cache_key, queryset, 300)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        craftsman = self.request.user.craftsman_profile

        # Filtre pentru UI
        context["categories"] = ServiceCategory.objects.all().order_by("name")
        context["counties"] = County.objects.values_list("name", flat=True).order_by("name")
        context["current_category"] = self.request.GET.get("category", "")
        context["current_county"] = self.request.GET.get("county", "")

        # Comenzi la care meșterul a fost invitat
        context["invited_order_ids"] = set(
            Invitation.objects.filter(craftsman=self.request.user).values_list("order_id", flat=True)
        )

        return context


class CreateQuoteView(LoginRequiredMixin, CreateView):
    model = Quote
    template_name = "services/create_quote.html"
    fields = ["price", "description", "estimated_duration"]

    # Rate limiting ELIMINAT - nu mai sunt restricții

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs["order_pk"])

        # Check if user is craftsman and order is published
        if request.user.user_type != "craftsman":
            messages.error(request, "Doar meșterii pot trimite oferte.")
            return redirect("services:order_detail", pk=self.order.pk)

        if self.order.status != "published":
            # Permite doar dacă există o invitație acceptată pentru acest meșter
            invitation = Invitation.objects.filter(order=self.order, craftsman=request.user, status="accepted").first()
            if not invitation:
                messages.error(request, "Nu poți trimite oferte pentru această comandă.")
                return redirect("services:order_detail", pk=self.order.pk)

        # Check if craftsman has complete profile (GATING)
        if not hasattr(request.user, "craftsman_profile"):
            messages.error(request, "Trebuie să îți completezi profilul de meșter mai întâi.")
            return redirect("accounts:edit_profile")

        craftsman_profile = request.user.craftsman_profile
        if not craftsman_profile.can_bid_on_jobs():
            missing_items = []
            if not craftsman_profile.profile_photo:
                missing_items.append("poză de profil")
            if craftsman_profile.portfolio_images.count() < 3:
                missing_items.append(f"{3 - craftsman_profile.portfolio_images.count()} poze portofoliu")
            if not craftsman_profile.bio or len(craftsman_profile.bio.strip()) < 200:
                missing_items.append("descriere completă (min. 200 caractere)")

            messages.error(request, "Profilul tău nu este complet: " + ", ".join(missing_items))
            return redirect("accounts:edit_profile")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        return context

    def form_valid(self, form):
        form.instance.craftsman = self.request.user.craftsman_profile
        form.instance.order = self.order

        # Additional validation: Prevent duplicate quotes
        if Quote.objects.filter(order=self.order, craftsman=self.request.user.craftsman_profile).exists():
            messages.error(self.request, "Ai trimis deja o ofertă pentru această comandă.")
            return redirect("services:order_detail", pk=self.order.pk)

        response = super().form_valid(form)
        messages.success(self.request, "Oferta a fost trimisă cu succes!")
        return response

    def get_success_url(self):
        return reverse_lazy("services:order_detail", kwargs={"pk": self.order.pk})


class PublishOrderView(LoginRequiredMixin, DetailView):
    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        # Check if user is the owner
        if order.client != request.user:
            messages.error(request, "Nu poți publica această comandă.")
            return redirect("services:order_detail", pk=order.pk)

        order.status = "published"
        order.published_at = timezone.now()
        order.save()

        messages.success(request, "Comanda a fost publicată și este acum disponibilă pentru oferte!")
        return redirect("services:order_detail", pk=order.pk)


class AcceptQuoteView(LoginRequiredMixin, DetailView):
    model = Quote

    def post(self, request, *args, **kwargs):
        quote = self.get_object()

        # Check if user is the order owner
        if quote.order.client != request.user:
            messages.error(request, "Nu poți accepta această ofertă.")
            return redirect("services:order_detail", pk=quote.order.pk)

        # Mark this quote as accepted and the rest as rejected
        quote.status = "accepted"
        quote.save()

        # Assign the craftsman to the order and update status
        order = quote.order
        order.assigned_craftsman = quote.craftsman
        order.status = "awaiting_confirmation"
        order.selected_at = timezone.now()
        order.save()

        # Notify the craftsman
        # (Handled by signals: handle_quote_notifications)

        messages.success(request, "Oferta a fost acceptată! Așteptăm confirmarea meșterului.")
        return redirect("services:order_detail", pk=order.pk)


class RejectQuoteView(LoginRequiredMixin, DetailView):
    model = Quote

    def post(self, request, *args, **kwargs):
        quote = self.get_object()

        # Check if user is the order owner
        if quote.order.client != request.user:
            messages.error(request, "Nu poți respinge această ofertă.")
            return redirect("services:order_detail", pk=quote.order.pk)

        # Mark this quote as rejected
        quote.status = "rejected"
        quote.save()

        # Notify the craftsman (handled by signals)

        messages.success(request, "Oferta a fost respinsă.")
        return redirect("services:order_detail", pk=quote.order.pk)


class ConfirmOrderView(LoginRequiredMixin, DetailView):
    """View for craftsmen to confirm they will take on an order"""

    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        # Check if user is the assigned craftsman
        if not hasattr(request.user, "craftsman_profile") or order.assigned_craftsman != request.user.craftsman_profile:
            messages.error(request, "Nu poți confirma această comandă.")
            return redirect("services:order_detail", pk=order.pk)

        # Check if order is awaiting confirmation
        if order.status != "awaiting_confirmation":
            messages.error(request, "Această comandă nu poate fi confirmată.")
            return redirect("services:order_detail", pk=order.pk)

        # Confirm the order
        order.status = "in_progress"
        order.confirmed_at = timezone.now()
        order.save()

        # Notification handled by signals on order status change

        messages.success(request, "Ai confirmat preluarea comenzii! Clientul va fi notificat.")
        return redirect("services:order_detail", pk=order.pk)


class DeclineOrderView(LoginRequiredMixin, DetailView):
    """View for craftsmen to decline an order after being selected"""

    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        # Check if user is the assigned craftsman
        if not hasattr(request.user, "craftsman_profile") or order.assigned_craftsman != request.user.craftsman_profile:
            messages.error(request, "Nu poți refuza această comandă.")
            return redirect("services:order_detail", pk=order.pk)

        # Check if order is awaiting confirmation
        if order.status != "awaiting_confirmation":
            messages.error(request, "Această comandă nu poate fi refuzată.")
            return redirect("services:order_detail", pk=order.pk)

        # Decline the order - reset to published status
        order.status = "published"
        order.assigned_craftsman = None
        order.selected_at = None
        order.save()

        # Reset the accepted quote back to pending
        accepted_quote = Quote.objects.filter(order=order, status="accepted").first()
        if accepted_quote:
            accepted_quote.status = "declined"
            accepted_quote.save()

        # Create notification for client
        NotificationService.create_notification(
            recipient=order.client,
            title="Meșterul a refuzat comanda",
            message=f'Din păcate, meșterul {request.user.get_full_name() or request.user.username} nu poate prelua comanda "{order.title}". Comanda a fost republicată pentru alte oferte.',
            notification_type="order_update",
            priority="medium",
            sender=request.user,
            action_url=f"/services/order/{order.pk}/",
            related_object_type="order",
            related_object_id=order.pk,
            data={"order_id": order.pk, "status": order.status},
        )

        messages.success(request, "Ai refuzat comanda. Clientul va fi notificat și comanda va fi republicată.")
        return redirect("services:available_orders")


class CreateReviewView(LoginRequiredMixin, CreateView):
    """Enhanced review creation with image upload support"""

    model = Review
    form_class = ReviewForm
    template_name = "services/create_review.html"

    def dispatch(self, request, *args, **kwargs):
        self.order = get_object_or_404(Order, pk=kwargs["pk"])

        # Check if user can review this order
        if self.order.client != request.user:
            messages.error(request, "Nu poți lăsa o recenzie pentru această comandă.")
            return redirect("services:order_detail", pk=self.order.pk)

        # Check if review already exists
        if hasattr(self.order, "review"):
            messages.info(request, "Ai lăsat deja o recenzie pentru această comandă.")
            return redirect("services:order_detail", pk=self.order.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = self.order
        context["image_form"] = MultipleReviewImageForm()
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
                ReviewImage.objects.create(review=self.object, image=image, description=f"Imagine {i + 1}")

        # Update craftsman ratings
        self._update_craftsman_ratings()

        # Update order status
        self.order.status = "completed"
        self.order.save()

        messages.success(self.request, "Recenzia a fost adăugată cu succes!")
        return response

    def _update_craftsman_ratings(self):
        """Update craftsman's average rating and review count"""
        craftsman = self.order.assigned_craftsman
        reviews = Review.objects.filter(craftsman=craftsman)

        # Calculate new averages
        avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0
        total_reviews = reviews.count()

        # Update craftsman profile
        craftsman.average_rating = round(avg_rating, 2)
        craftsman.total_reviews = total_reviews
        craftsman.save()

    def get_success_url(self):
        return reverse_lazy("services:order_detail", kwargs={"pk": self.order.pk})


class ReviewDetailView(DetailView):
    """View for displaying individual review details"""

    model = Review
    template_name = "services/review_detail.html"
    context_object_name = "review"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["review_images"] = self.object.images.all()
        return context


class CraftsmanReviewsView(ListView):
    """View for displaying all reviews for a craftsman"""

    model = Review
    template_name = "services/craftsman_reviews.html"
    context_object_name = "reviews"
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.craftsman = get_object_or_404(CraftsmanProfile, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Review.objects.filter(craftsman=self.craftsman).select_related("client", "order").prefetch_related("images")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["craftsman"] = self.craftsman

        # Calculate review statistics
        reviews = self.get_queryset()
        context["total_reviews"] = reviews.count()
        context["average_rating"] = reviews.aggregate(Avg("rating"))["rating__avg"] or 0

        # Rating distribution
        rating_counts = {}
        for i in range(1, 6):
            rating_counts[i] = reviews.filter(rating=i).count()
        context["rating_distribution"] = rating_counts

        return context


class ReviewImageUploadView(LoginRequiredMixin, CreateView):
    """View for uploading additional review images"""

    model = ReviewImage
    form_class = ReviewImageForm
    template_name = "services/upload_review_image.html"

    def dispatch(self, request, *args, **kwargs):
        self.review = get_object_or_404(Review, pk=kwargs["review_pk"])

        # Check if user owns this review
        if self.review.client != request.user:
            messages.error(request, "Nu poți adăuga imagini la această recenzie.")
            return redirect("services:review_detail", pk=self.review.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.review = self.review
        messages.success(self.request, "Imaginea a fost adăugată la recenzie.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("services:review_detail", kwargs={"pk": self.review.pk})


LEAD_FEE_CENTS = 2000  # 20 lei exemplu


class InviteCraftsmenView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "services/invite_craftsmen.html"
    context_object_name = "order"

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()

        # Only the owner can invite craftsmen
        if order.client != request.user:
            messages.error(request, "Nu poți invita meșteri pentru această comandă.")
            return redirect("services:order_detail", pk=order.pk)

        # Check if order is published
        if order.status != "published":
            messages.error(request, "Comanda trebuie să fie publicată pentru a invita meșteri.")
            return redirect("services:order_detail", pk=order.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()

        # Get craftsmen in the same category and area
        craftsmen = (
            CraftsmanProfile.objects.filter(
                services__service__category=order.service.category, user__user_type="craftsman"
            )
            .select_related("user", "county", "city")
            .distinct()
        )

        # Filter by location if coverage area exists
        # TODO: Implement distance-based filtering

        # Exclude already invited craftsmen
        invited_craftsmen_ids = order.invitations.values_list("craftsman_id", flat=True)
        craftsmen = craftsmen.exclude(user_id__in=invited_craftsmen_ids)

        # Exclude craftsmen who already quoted
        quoted_craftsmen_ids = order.quotes.values_list("craftsman__user_id", flat=True)
        craftsmen = craftsmen.exclude(user_id__in=quoted_craftsmen_ids)

        context["craftsmen"] = craftsmen[:20]  # Limit to 20 for performance
        context["invited_count"] = order.invitations.count()

        return context

    def post(self, request, *args, **kwargs):
        """Handle craftsman invitations"""
        order = self.get_object()
        craftsman_ids = request.POST.getlist("craftsman_ids")

        invited_count = 0
        for craftsman_id in craftsman_ids:
            try:
                craftsman = get_object_or_404(CraftsmanProfile, user_id=craftsman_id)
                invitation, created = Invitation.objects.get_or_create(
                    order=order, craftsman=craftsman.user, defaults={"invited_by": request.user}
                )
                if created:
                    invited_count += 1
                    # TODO: Send notification to craftsman
            except (Http404, ValueError) as e:
                logger.warning(f"Failed to invite craftsman {craftsman_id}: {e}")
                continue
            except Exception as e:
                logger.exception(f"Unexpected error inviting craftsman {craftsman_id}: {e}")
                continue

        if invited_count > 0:
            messages.success(request, f"Au fost invitați {invited_count} meșteri să oferteze.")
        else:
            messages.info(request, "Nu au fost invitați meșteri noi.")

        return redirect("services:order_detail", pk=order.pk)


class AcceptInvitationView(LoginRequiredMixin, DetailView):
    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        # Doar meșterii pot răspunde la invitații
        if getattr(request.user, "user_type", None) != "craftsman":
            messages.error(request, "Doar meșterii pot răspunde la invitații.")
            return redirect("services:order_detail", pk=order.pk)

        # Găsește invitația
        invitation = Invitation.objects.filter(order=order, craftsman=request.user).first()
        if not invitation:
            messages.error(request, "Nu există invitație pentru această comandă.")
            return redirect("services:order_detail", pk=order.pk)

        # Acceptă invitația
        invitation.status = "accepted"
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=["status", "responded_at"])

        # Notifică clientul
        NotificationService.create_notification(
            recipient=order.client,
            title="Meșterul a acceptat invitația",
            message=f'{request.user.get_full_name() or request.user.username} a acceptat invitația pentru "{order.title}".',
            notification_type="order",
            priority="medium",
            sender=request.user,
            action_url=f"/services/order/{order.pk}/",
            related_object_type="order",
            related_object_id=order.pk,
            data={"order_id": order.pk, "invitation_status": "accepted"},
        )

        messages.success(request, "Ai acceptat invitația. Poți trimite o ofertă!")
        return redirect("services:order_detail", pk=order.pk)


class DeclineInvitationView(LoginRequiredMixin, DetailView):
    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        if getattr(request.user, "user_type", None) != "craftsman":
            messages.error(request, "Doar meșterii pot răspunde la invitații.")
            return redirect("services:order_detail", pk=order.pk)

        invitation = Invitation.objects.filter(order=order, craftsman=request.user).first()
        if not invitation:
            messages.error(request, "Nu există invitație pentru această comandă.")
            return redirect("services:order_detail", pk=order.pk)

        # Refuză invitația
        invitation.status = "declined"
        invitation.responded_at = timezone.now()
        invitation.save(update_fields=["status", "responded_at"])

        # Notifică clientul
        NotificationService.create_notification(
            recipient=order.client,
            notification_type="order_declined",
            title="Meșterul a refuzat invitația",
            message=f'{request.user.get_full_name() or request.user.username} a refuzat invitația pentru "{order.title}".',
            order=order,
        )

        messages.info(request, "Ai refuzat invitația.")
        return redirect("services:available_orders")


class ShortlistCraftsmanView(LoginRequiredMixin, DetailView):
    model = Order

    def post(self, request, *args, **kwargs):
        from .lead_fee_service import InsufficientBalanceError, LeadFeeService

        order = self.get_object()

        # Only the order owner can shortlist craftsmen
        if order.client != request.user:
            messages.error(request, "Nu poți adăuga meșteri pe lista scurtă pentru această comandă.")
            return redirect("services:order_detail", pk=order.pk)

        craftsman_id = request.POST.get("craftsman_id")
        if not craftsman_id:
            messages.error(request, "Meșterul nu a fost specificat.")
            return redirect("services:invite_craftsmen", pk=order.pk)

        try:
            # Get craftsman profile
            craftsman_profile = get_object_or_404(CraftsmanProfile, pk=craftsman_id)
            craftsman_user = craftsman_profile.user

            # Check if already shortlisted
            existing_shortlist = Shortlist.objects.filter(order=order, craftsman=craftsman_user).first()

            if existing_shortlist:
                messages.info(request, "Acest meșter este deja pe lista scurtă.")
                return redirect("services:invite_craftsmen", pk=order.pk)

            # Attempt to charge lead fee and create shortlist
            shortlist = LeadFeeService.charge_shortlist_fee(order=order, craftsman_user=craftsman_user)

            messages.success(
                request,
                f"Meșterul {craftsman_profile.display_name or craftsman_user.username} "
                f"a fost adăugat pe lista scurtă! Taxa de {shortlist.lead_fee_lei:.0f} RON "
                "a fost dedusă din wallet-ul meșterului.",
            )

        except InsufficientBalanceError as e:
            messages.error(
                request,
                f"Meșterul nu are suficient credit în wallet pentru această comandă. "
                f"Sold necesar: {e.required_cents/100:.0f} RON, "
                f"disponibil: {e.available_cents/100:.0f} RON.",
            )

        except ValueError as e:
            messages.error(request, f"Eroare: {str(e)}")

        except Exception as e:
            logger.error(f"Error in ShortlistCraftsmanView: {e}", exc_info=True)
            messages.error(request, "A apărut o eroare la adăugarea meșterului pe lista scurtă.")

        return redirect("services:invite_craftsmen", pk=order.pk)


class WalletView(LoginRequiredMixin, DetailView):
    model = CreditWallet
    template_name = "services/wallet.html"

    def get_object(self):
        from .wallet_service import get_or_create_wallet
        # Use service layer for safe wallet retrieval
        return get_or_create_wallet(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["transactions"] = WalletTransaction.objects.filter(wallet=self.object).order_by("-created_at")
        return context


# Craftsman Services Management Views


class CraftsmanServicesView(CraftsmanRequiredMixin, ListView):
    """View for craftsmen to manage their services"""

    model = CraftsmanService
    template_name = "services/craftsman_services.html"
    context_object_name = "services"
    paginate_by = 20

    def get_queryset(self):
        return CraftsmanService.objects.filter(craftsman=self.request.user.craftsman_profile).select_related(
            "service__category"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["craftsman"] = self.request.user.craftsman_profile
        context["total_services"] = self.get_queryset().count()
        return context


class AddCraftsmanServiceView(CraftsmanRequiredMixin, CreateView):
    """View for craftsmen to add new services"""

    model = CraftsmanService
    form_class = CraftsmanServiceForm
    template_name = "services/add_craftsman_service.html"

    def form_valid(self, form):
        form.instance.craftsman = self.request.user.craftsman_profile

        # Check if service already exists for this craftsman
        if CraftsmanService.objects.filter(
            craftsman=self.request.user.craftsman_profile, service=form.cleaned_data["service"]
        ).exists():
            messages.error(self.request, "Ai adăugat deja acest serviciu.")
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, "Serviciul a fost adăugat cu succes!")
        return response

    def get_success_url(self):
        return reverse_lazy("services:craftsman_services")


class EditCraftsmanServiceView(CraftsmanRequiredMixin, UpdateView):
    """View for craftsmen to edit their services"""

    model = CraftsmanService
    form_class = CraftsmanServiceForm
    template_name = "services/edit_craftsman_service.html"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        # If the parent dispatch returned a redirect, return it
        if hasattr(response, "status_code") and response.status_code == 302:
            return response

        service = self.get_object()

        # Only allow the owner to edit
        if service.craftsman.user != request.user:
            messages.error(request, "Nu poți edita acest serviciu.")
            return redirect("services:craftsman_services")

        return response

    def get_queryset(self):
        return CraftsmanService.objects.filter(craftsman=self.request.user.craftsman_profile)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Serviciul a fost actualizat cu succes!")
        return response

    def get_success_url(self):
        return reverse_lazy("services:craftsman_services")


class DeleteCraftsmanServiceView(CraftsmanRequiredMixin, DetailView):
    """View for craftsmen to delete their services"""

    model = CraftsmanService

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        # If the parent dispatch returned a redirect, return it
        if hasattr(response, "status_code") and response.status_code == 302:
            return response

        service = self.get_object()

        # Only allow the owner to delete
        if service.craftsman.user != request.user:
            messages.error(request, "Nu poți șterge acest serviciu.")
            return redirect("services:craftsman_services")

        return response

    def post(self, request, *args, **kwargs):
        service = self.get_object()
        service_name = service.service.name
        service.delete()

        messages.success(request, f'Serviciul "{service_name}" a fost șters cu succes!')
        return redirect("services:craftsman_services")

    def get_queryset(self):
        return CraftsmanService.objects.filter(craftsman=self.request.user.craftsman_profile)


class NotificationsView(LoginRequiredMixin, ListView):
    """View for displaying user notifications"""

    model = Notification
    template_name = "services/notifications.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Count unread notifications
        unread_count = Notification.objects.filter(recipient=self.request.user, is_read=False).count()

        context["unread_count"] = unread_count
        return context

    def get(self, request, *args, **kwargs):
        # Mark all notifications as read when viewing the page
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())

        return super().get(request, *args, **kwargs)
