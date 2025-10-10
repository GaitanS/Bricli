from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("how-it-works/", views.HowItWorksView.as_view(), name="how_it_works"),
    path("faq/", views.FAQView.as_view(), name="faq"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("search/", views.SearchView.as_view(), name="search"),
    # Legal pages
    path("terms/", views.TermsView.as_view(), name="terms"),
    path("privacy/", views.PrivacyView.as_view(), name="privacy"),
    # Debug preview routes (safe to keep under DEBUG only usage)
    path("debug/404/", views.preview_404, name="preview_404"),
]
