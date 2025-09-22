from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.db.models import Q
from services.models import ServiceCategory, Order
from accounts.models import CraftsmanProfile, County, City
from .models import SiteSettings, Testimonial, FAQ


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get site settings
        try:
            site_settings = SiteSettings.objects.first()
        except SiteSettings.DoesNotExist:
            site_settings = None

        context.update({
            'site_settings': site_settings,
            'service_categories': ServiceCategory.objects.filter(is_active=True)[:8],
            'featured_testimonials': Testimonial.objects.filter(is_featured=True)[:3],
            'recent_orders': Order.objects.filter(status='published')[:6],
            'top_craftsmen': CraftsmanProfile.objects.filter(
                user__is_verified=True
            ).order_by('-average_rating', '-total_reviews')[:6],
            'counties': County.objects.all()[:10],  # Popular counties
        })
        return context


class AboutView(TemplateView):
    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            site_settings = SiteSettings.objects.first()
        except SiteSettings.DoesNotExist:
            site_settings = None
        context['site_settings'] = site_settings
        return context


class HowItWorksView(TemplateView):
    template_name = 'core/how_it_works.html'


class FAQView(ListView):
    model = FAQ
    template_name = 'core/faq.html'
    context_object_name = 'faqs'

    def get_queryset(self):
        return FAQ.objects.filter(is_active=True)


class ContactView(TemplateView):
    template_name = 'core/contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            site_settings = SiteSettings.objects.first()
        except SiteSettings.DoesNotExist:
            site_settings = None
        context['site_settings'] = site_settings
        return context


class SearchView(ListView):
    """Enhanced search view with intelligent matching for craftsmen"""
    template_name = 'core/search.html'
    context_object_name = 'craftsmen'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        county_id = self.request.GET.get('county', '')
        rating_min = self.request.GET.get('rating', '')

        # Base queryset with active craftsmen
        queryset = CraftsmanProfile.objects.filter(
            user__is_active=True
        ).select_related('user', 'county', 'city')

        # Enhanced search with weighted scoring
        if query:
            # Primary matches (higher weight)
            primary_matches = Q(description__icontains=query)

            # Secondary matches (medium weight)
            secondary_matches = (
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(company_name__icontains=query)
            )

            # Apply search filters
            queryset = queryset.filter(primary_matches | secondary_matches)

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
            '-user__is_verified',      # Verified craftsmen first
            '-average_rating',         # Higher rated craftsmen
            '-total_reviews',          # More reviewed craftsmen
            '-total_jobs_completed',   # More experienced craftsmen
            '-user__date_joined'       # Newer members last
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        county_id = self.request.GET.get('county', '')
        rating_min = self.request.GET.get('rating', '')

        # Get county object if specified
        county = None
        if county_id:
            try:
                county = County.objects.get(id=int(county_id))
            except (County.DoesNotExist, ValueError, TypeError):
                pass

        # Calculate search statistics
        total_craftsmen = CraftsmanProfile.objects.filter(user__is_active=True).count()
        verified_craftsmen = CraftsmanProfile.objects.filter(
            user__is_active=True,
            user__is_verified=True
        ).count()

        context.update({
            'query': query,
            'county': county,
            'rating_min': rating_min,
            'counties': County.objects.all().order_by('name'),
            'total_craftsmen': total_craftsmen,
            'verified_craftsmen': verified_craftsmen,
            'search_performed': bool(query or county_id or rating_min),
        })
        return context
