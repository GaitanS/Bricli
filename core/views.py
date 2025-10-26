from django.contrib import messages
from django.db import models
from django.db.models import Avg, Count, Q
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.text import slugify
from django.views.generic import ListView, TemplateView, DetailView

from accounts.models import County, CraftsmanProfile
from services.models import Order, Review, Service, ServiceCategory

from .filters import get_county_by_any, sanitize_query
from .models import FAQ, SiteSettings, Testimonial, CityLandingPage


def preview_404(request):
    """Render custom 404 template for preview while DEBUG=True."""
    response = render(request, "404.html", status=404)
    return response


class HomeView(TemplateView):
    template_name = "core/home.html"

    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated craftsmen to their dashboard"""
        if request.user.is_authenticated and getattr(request.user, "user_type", None) == "craftsman":
            return redirect("services:my_quotes")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from django.conf import settings

        context = super().get_context_data(**kwargs)

        # Get site settings
        try:
            site_settings = SiteSettings.objects.first()
        except SiteSettings.DoesNotExist:
            site_settings = None

        # Calculate platform statistics
        active_craftsmen = CraftsmanProfile.objects.filter(user__is_active=True, user__is_verified=True).count()
        avg_rating_data = Review.objects.aggregate(avg=Avg("rating"))
        avg_rating = avg_rating_data["avg"] or 0.0
        completed_projects = Order.objects.filter(status="completed").count()

        # BETA MODE: Count registered BETA members
        beta_count = 0
        if not settings.SUBSCRIPTIONS_ENABLED:
            beta_count = CraftsmanProfile.objects.filter(beta_member=True).count()

        context.update(
            {
                "site_settings": site_settings,
                "service_categories": ServiceCategory.objects.filter(is_active=True).annotate(
                    orders_count=models.Count("services__order", filter=models.Q(services__order__status="published"))
                )[:8],
                "featured_testimonials": Testimonial.objects.filter(is_featured=True)[:3],
                # Phase 9: Prioritize Pro members in featured craftsmen
                "top_craftsmen": CraftsmanProfile.objects.filter(user__is_verified=True)
                .select_related("subscription", "subscription__tier")
                .annotate(
                    tier_priority=models.Case(
                        models.When(subscription__tier__name='pro', then=models.Value(0)),
                        models.When(subscription__tier__name='plus', then=models.Value(1)),
                        models.When(subscription__tier__name='free', then=models.Value(2)),
                        default=models.Value(3),
                        output_field=models.IntegerField(),
                    )
                ).order_by(
                    "tier_priority",  # Pro > Plus > Free
                    "-average_rating",
                    "-total_reviews"
                )[:6],
                "counties": County.objects.all().order_by("name"),  # All counties
                # Platform statistics
                "stats": {
                    "active_craftsmen": active_craftsmen,
                    "avg_rating": round(avg_rating, 1) if avg_rating else 0,
                    "completed_projects": completed_projects,
                },
                # BETA MODE: Counter for first 100 members
                "beta_count": beta_count,
            }
        )
        return context


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            site_settings = SiteSettings.objects.first()
        except SiteSettings.DoesNotExist:
            site_settings = None
        context["site_settings"] = site_settings
        return context


class HowItWorksView(TemplateView):
    template_name = "core/how_it_works.html"


class FAQView(ListView):
    model = FAQ
    template_name = "core/faq.html"
    context_object_name = "faqs"

    def get_queryset(self):
        return FAQ.objects.filter(is_active=True)


class ContactView(TemplateView):
    template_name = "core/contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            site_settings = SiteSettings.objects.first()
        except SiteSettings.DoesNotExist:
            site_settings = None
        context["site_settings"] = site_settings
        return context


class SearchView(ListView):
    """Enhanced search view with intelligent matching for craftsmen"""

    template_name = "core/search.html"
    context_object_name = "craftsmen"
    paginate_by = 60  # Default, can be overridden by per_page parameter

    def get_paginate_by(self, queryset):
        """Override pagination based on per_page query parameter"""
        per_page = self.request.GET.get("per_page", "60")
        try:
            per_page_int = int(per_page)
            # Validate per_page is one of allowed values
            if per_page_int in [60, 80, 100]:
                return per_page_int
        except (ValueError, TypeError):
            pass
        return 60  # Default fallback

    def get_queryset(self):
        query = sanitize_query(self.request.GET.get("q", ""))
        county_param = self.request.GET.get("county", "")
        category_param = self.request.GET.get("category", "")
        rating_min = self.request.GET.get("rating", "")

        # Base queryset with active craftsmen
        # Phase 9: Include subscription data for tier badges
        queryset = (
            CraftsmanProfile.objects.filter(user__is_active=True)
            .select_related("user", "county", "city", "subscription", "subscription__tier")
            .prefetch_related("services", "services__service", "services__service__category")
        )

        # Enhanced search with weighted scoring
        if query:
            # Primary matches (higher weight)
            primary_matches = Q(bio__icontains=query)

            # Secondary matches (medium weight)
            secondary_matches = (
                Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(display_name__icontains=query)
            )

            # Normalize query to slug form to be accent-insensitive (e.g., "amenajare gradina" -> "amenajare-gradina")
            normalized_query = slugify(query)

            # Service matches by name/category
            service_matches = Q(services__service__name__icontains=query) | Q(
                services__service__category__name__icontains=query
            )

            # Service matches by slug (accent-insensitive)
            service_slug_matches = Q(services__service__slug__icontains=normalized_query) | Q(
                services__service__category__slug__icontains=normalized_query
            )

            # Token-based matching: split normalized query into tokens and match each token
            tokens = [t for t in normalized_query.replace("-", " ").split() if t]
            token_matches = Q()

            # Common Romanian diacritics/synonyms variants for better matching
            synonyms_map = {
                "gradina": ["gradina", "grădină", "gradinarit", "grădinărit"],
                "acoperis": ["acoperis", "acoperiș"],
                "instalatii": ["instalatii", "instalații"],
            }

            for t in tokens:
                variants = synonyms_map.get(t, [t])
                for v in variants:
                    token_matches |= (
                        Q(services__service__slug__icontains=v)
                        | Q(services__service__name__icontains=v)
                        | Q(services__service__category__slug__icontains=v)
                        | Q(services__service__category__name__icontains=v)
                    )

            # Optional: match in service or category descriptions
            service_desc_matches = Q(services__service__description__icontains=query) | Q(
                services__service__category__description__icontains=query
            )

            # Apply search filters including services and ensure distinct results
            queryset = queryset.filter(
                primary_matches
                | secondary_matches
                | service_matches
                | service_slug_matches
                | token_matches
                | service_desc_matches
            ).distinct()

        # Location filtering - accepts id, slug, or name
        county = get_county_by_any(county_param)
        if county:
            queryset = queryset.filter(county=county)

        # Category filtering - filter by service category slug
        if category_param:
            from .filters import normalize_slug

            normalized_category = normalize_slug(category_param)

            # Validate against active categories
            valid_slugs = set(ServiceCategory.objects.filter(is_active=True).values_list("slug", flat=True))

            if normalized_category in valid_slugs:
                queryset = queryset.filter(services__service__category__slug=normalized_category).distinct()

        # Rating filtering
        if rating_min:
            try:
                rating_min = float(rating_min)
                queryset = queryset.filter(average_rating__gte=rating_min)
            except (ValueError, TypeError):
                pass

        # Sorting based on sort parameter
        sort_by = self.request.GET.get("sort", "popular")

        # Define sort order based on sort_by parameter
        if sort_by == "newest":
            # Newest craftsmen first
            queryset = queryset.order_by("-user__date_joined")
        elif sort_by == "reviews":
            # Most reviewed craftsmen first
            queryset = queryset.order_by("-total_reviews", "-average_rating")
        elif sort_by == "rating":
            # Highest rated craftsmen first
            queryset = queryset.order_by("-average_rating", "-total_reviews")
        else:  # Default: "popular"
            # Phase 9: Intelligent ordering with subscription tier priority
            from django.db.models import Case, When, Value, IntegerField
            queryset = queryset.annotate(
                tier_priority=Case(
                    When(subscription__tier__name='pro', then=Value(0)),
                    When(subscription__tier__name='plus', then=Value(1)),
                    When(subscription__tier__name='free', then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).order_by(
                "tier_priority",  # Pro > Plus > Free
                "-user__is_verified",  # Verified craftsmen first
                "-average_rating",  # Higher rated craftsmen
                "-total_reviews",  # More reviewed craftsmen
                "-total_jobs_completed",  # More experienced craftsmen
                "-user__date_joined",  # Newer members last
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = sanitize_query(self.request.GET.get("q", ""))
        county_param = self.request.GET.get("county", "")
        category_param = self.request.GET.get("category", "")
        rating_min = self.request.GET.get("rating", "")
        sort_by = self.request.GET.get("sort", "popular")
        # view_mode = self.request.GET.get("view", "grid")  # REMOVED: View toggle eliminated
        per_page = self.get_paginate_by(None)

        # Get county object if specified (by id, slug, or name)
        county = get_county_by_any(county_param)

        # Get active category if specified
        from .filters import normalize_slug

        active_category = None
        if category_param:
            normalized_category = normalize_slug(category_param)
            try:
                active_category = ServiceCategory.objects.get(slug=normalized_category, is_active=True)
            except ServiceCategory.DoesNotExist:
                pass

        # Calculate search statistics
        total_craftsmen = CraftsmanProfile.objects.filter(user__is_active=True).count()
        verified_craftsmen = CraftsmanProfile.objects.filter(user__is_active=True, user__is_verified=True).count()

        # Calculate rating bucket counts (BEFORE applying rating filter)
        # This shows how many results would appear at each rating threshold
        rating_counts = {}
        rating_thresholds = [3.0, 3.5, 4.0, 4.5, 5.0]

        # Build base queryset without rating filter for counting
        base_queryset_for_rating = CraftsmanProfile.objects.filter(user__is_active=True)

        # Apply same filters as main queryset (query, county, category) but NOT rating
        if query:
            # Reuse same search logic as get_queryset()
            primary_matches = Q(bio__icontains=query)
            secondary_matches = (
                Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(display_name__icontains=query)
            )
            normalized_query = slugify(query)
            service_matches = Q(services__service__name__icontains=query) | Q(
                services__service__category__name__icontains=query
            )
            service_slug_matches = Q(services__service__slug__icontains=normalized_query) | Q(
                services__service__category__slug__icontains=normalized_query
            )
            tokens = [t for t in normalized_query.replace("-", " ").split() if t]
            token_matches = Q()
            synonyms_map = {
                "gradina": ["gradina", "grădină", "gradinarit", "grădinărit"],
                "acoperis": ["acoperis", "acoperiș"],
                "instalatii": ["instalatii", "instalații"],
            }
            for t in tokens:
                variants = synonyms_map.get(t, [t])
                for v in variants:
                    token_matches |= (
                        Q(services__service__slug__icontains=v)
                        | Q(services__service__name__icontains=v)
                        | Q(services__service__category__slug__icontains=v)
                        | Q(services__service__category__name__icontains=v)
                    )
            service_desc_matches = Q(services__service__description__icontains=query) | Q(
                services__service__category__description__icontains=query
            )
            base_queryset_for_rating = base_queryset_for_rating.filter(
                primary_matches
                | secondary_matches
                | service_matches
                | service_slug_matches
                | token_matches
                | service_desc_matches
            ).distinct()

        if county:
            base_queryset_for_rating = base_queryset_for_rating.filter(county=county)

        if category_param and active_category:
            base_queryset_for_rating = base_queryset_for_rating.filter(
                services__service__category__slug=active_category.slug
            ).distinct()

        # Count craftsmen at each rating threshold
        for threshold in rating_thresholds:
            rating_counts[threshold] = base_queryset_for_rating.filter(average_rating__gte=threshold).count()

        context.update(
            {
                "query": query,
                "county": county,
                "county_param": county_param,  # Pass original param for form preservation
                "active_category": active_category,
                "category_param": category_param,
                "rating_min": rating_min,
                "rating_counts": rating_counts,  # Pass rating bucket counts to template
                "sort_by": sort_by,  # Current sort option
                # "view_mode": view_mode,  # REMOVED: View toggle eliminated
                "per_page": per_page,  # Current per-page setting
                "counties": County.objects.all().order_by("name"),
                "total_craftsmen": total_craftsmen,
                "verified_craftsmen": verified_craftsmen,
                "search_performed": bool(query or county or active_category or rating_min),
                # Suggestions sidebar data
                "service_categories": ServiceCategory.objects.filter(is_active=True).order_by("name"),
                "popular_services": Service.objects.filter(is_popular=True, is_active=True).order_by("name")[:30],
            }
        )
        return context


class TermsView(TemplateView):
    template_name = "legal/terms.html"


class PrivacyView(TemplateView):
    template_name = "legal/privacy.html"


def custom_404_view(request, exception):
    """Custom 404 error handler"""
    return render(request, "404.html", status=404)


def custom_500_view(request):
    """Custom 500 error handler"""
    return render(request, "500.html", status=500)


class CityLandingPageView(DetailView):
    """
    SEO landing pages pentru căutări locale: instalator-brasov, electrician-bucuresti, etc.
    """
    model = CityLandingPage
    template_name = 'core/city_landing.html'
    context_object_name = 'page'

    def get_object(self):
        return get_object_or_404(
            CityLandingPage,
            profession_slug=self.kwargs['profession_slug'],
            city_slug=self.kwargs['city_slug'],
            is_active=True
        )

    def markdown_to_html(self, text):
        """Convert simple markdown to HTML"""
        import re
        if not text:
            return ''

        # Convert **text** to <strong>text</strong>
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        # Convert lines starting with - to <ul><li>
        lines = text.split('\n')
        html_lines = []
        in_list = False

        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                if not in_list:
                    html_lines.append('<ul class="list-unstyled">')
                    in_list = True
                # Remove the - and wrap in li
                html_lines.append(f'<li class="mb-2"><i class="fas fa-check-circle text-primary me-2"></i>{line[2:]}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                if line:
                    html_lines.append(f'<p>{line}</p>')

        if in_list:
            html_lines.append('</ul>')

        return '\n'.join(html_lines)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = self.object

        # Convert markdown to HTML for all text fields
        context['services_html'] = self.markdown_to_html(page.services_text)
        context['prices_html'] = self.markdown_to_html(page.prices_text)
        context['how_it_works_html'] = self.markdown_to_html(page.how_it_works_text)

        # Comenzi recente din oraș (pentru sidebar)
        # Caută în city.name sau address
        from django.db.models import Q
        context['recent_orders'] = Order.objects.filter(
            Q(city__name__icontains=page.city_name) | Q(address__icontains=page.city_name),
            status__in=['open', 'published']
        ).select_related('city', 'service').order_by('-created_at')[:5]

        # Categorii de servicii pentru cross-linking
        context['service_categories'] = ServiceCategory.objects.filter(is_active=True)[:8]

        # Featured testimonials for SEO (Schema.org Review markup)
        context['testimonials'] = Testimonial.objects.filter(is_featured=True)[:3]

        return context
