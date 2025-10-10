from django.db import models
from django.db.models import Avg, Q
from django.shortcuts import render
from django.utils.text import slugify
from django.views.generic import ListView, TemplateView

from accounts.models import County, CraftsmanProfile
from services.models import Order, Review, ServiceCategory

from .models import FAQ, SiteSettings, Testimonial


def preview_404(request):
    """Render custom 404 template for preview while DEBUG=True."""
    response = render(request, "404.html", status=404)
    return response


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
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

        context.update(
            {
                "site_settings": site_settings,
                "service_categories": ServiceCategory.objects.filter(is_active=True).annotate(
                    orders_count=models.Count("services__order", filter=models.Q(services__order__status="published"))
                )[:8],
                "featured_testimonials": Testimonial.objects.filter(is_featured=True)[:3],
                "top_craftsmen": CraftsmanProfile.objects.filter(user__is_verified=True).order_by(
                    "-average_rating", "-total_reviews"
                )[:6],
                "counties": County.objects.all().order_by("name"),  # All counties
                # Platform statistics
                "stats": {
                    "active_craftsmen": active_craftsmen,
                    "avg_rating": round(avg_rating, 1) if avg_rating else 0,
                    "completed_projects": completed_projects,
                },
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
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get("q", "")
        county_id = self.request.GET.get("county", "")
        rating_min = self.request.GET.get("rating", "")

        # Base queryset with active craftsmen
        queryset = (
            CraftsmanProfile.objects.filter(user__is_active=True)
            .select_related("user", "county", "city")
            .prefetch_related("services", "services__service")
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

        # Location filtering
        if county_id:
            try:
                county_id = int(county_id)
                queryset = queryset.filter(county_id=county_id)
            except (ValueError, TypeError):
                pass

        # Rating filtering
        if rating_min:
            try:
                rating_min = float(rating_min)
                queryset = queryset.filter(average_rating__gte=rating_min)
            except (ValueError, TypeError):
                pass

        # Intelligent ordering with multiple factors
        return queryset.order_by(
            "-user__is_verified",  # Verified craftsmen first
            "-average_rating",  # Higher rated craftsmen
            "-total_reviews",  # More reviewed craftsmen
            "-total_jobs_completed",  # More experienced craftsmen
            "-user__date_joined",  # Newer members last
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "")
        county_id = self.request.GET.get("county", "")
        rating_min = self.request.GET.get("rating", "")

        # Get county object if specified
        county = None
        if county_id:
            try:
                county = County.objects.get(id=int(county_id))
            except (County.DoesNotExist, ValueError, TypeError):
                pass

        # Calculate search statistics
        total_craftsmen = CraftsmanProfile.objects.filter(user__is_active=True).count()
        verified_craftsmen = CraftsmanProfile.objects.filter(user__is_active=True, user__is_verified=True).count()

        context.update(
            {
                "query": query,
                "county": county,
                "rating_min": rating_min,
                "counties": County.objects.all().order_by("name"),
                "total_craftsmen": total_craftsmen,
                "verified_craftsmen": verified_craftsmen,
                "search_performed": bool(query or county_id or rating_min),
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
