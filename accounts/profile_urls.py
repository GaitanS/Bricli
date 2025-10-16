"""
Profile and Craftsmen URLs (mounted at /conturi/)
Namespace: 'accounts'
"""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Profile management
    path("profil/", views.ProfileView.as_view(), name="profile"),
    path("profil/editare/", views.EditProfileView.as_view(), name="edit_profile"),
    # Craftsmen directory - ASCII URLs (meșter→meserias, meșteri→meseriasi)
    path("meseriasi/", views.CraftsmenListView.as_view(), name="craftsmen_list"),
    path("meserias/<int:pk>/", views.CraftsmanIdRedirectView.as_view(), name="craftsman_by_id"),  # 301 redirect to slug
    path("meserias/<slug:slug>/", views.CraftsmanDetailView.as_view(), name="craftsman_detail"),
    # Portfolio management
    path("portofoliu/", views.CraftsmanPortfolioView.as_view(), name="portfolio"),
    path("portofoliu/gestionare/", views.ManagePortfolioView.as_view(), name="manage_portfolio"),
    path("portofoliu/incarcare/", views.PortfolioUploadView.as_view(), name="portfolio_upload"),
    path("portofoliu/incarcare-multipla/", views.BulkPortfolioUploadView.as_view(), name="bulk_portfolio_upload"),
    path("portofoliu/stergere/<int:pk>/", views.PortfolioDeleteView.as_view(), name="portfolio_delete"),
    # Onboarding
    path("integrare/", views.CraftsmanOnboardingView.as_view(), name="onboarding"),
    # AJAX validation endpoints
    path("api/validare-email/", views.validate_email_ajax, name="validate_email_ajax"),
    path("api/validare-telefon/", views.validate_phone_ajax, name="validate_phone_ajax"),
    # AJAX reviews endpoint
    path("craftsman/<int:pk>/reviews/", views.craftsman_reviews_ajax, name="craftsman_reviews_ajax"),
]
