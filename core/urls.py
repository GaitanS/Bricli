from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("despre/", views.AboutView.as_view(), name="about"),
    path("cum-functioneaza/", views.HowItWorksView.as_view(), name="how_it_works"),
    path("intrebari-frecvente/", views.FAQView.as_view(), name="faq"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("cautare/", views.SearchView.as_view(), name="search"),
    # Pagini legale
    path("termeni/", views.TermsView.as_view(), name="terms"),
    path("confidentialitate/", views.PrivacyView.as_view(), name="privacy"),
    # Rute debug preview (sigur să păstrezi doar sub DEBUG=True)
    path("debug/404/", views.preview_404, name="preview_404"),
    # SEO City Landing Pages - IMPORTANT: Must be last to avoid conflicts
    path("<slug:profession_slug>-<slug:city_slug>/", views.CityLandingPageView.as_view(), name="city_landing"),
]
