from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Înregistrare simplificată (stil MyHammer)
    path("inregistrare/", views.SimpleRegisterView.as_view(), name="register"),
    path("inregistrare/mester/", views.SimpleCraftsmanRegisterView.as_view(), name="craftsman_register"),
    path("inregistrare/simpla/", views.SimpleRegisterView.as_view(), name="simple_register"),
    path("inregistrare/simpla/mester/", views.SimpleCraftsmanRegisterView.as_view(), name="simple_craftsman_register"),
    # Formulare complete de înregistrare
    path("inregistrare/completa/", views.RegisterView.as_view(), name="full_register"),
    path("inregistrare/completa/mester/", views.CraftsmanRegisterView.as_view(), name="full_craftsman_register"),
    # Autentificare
    path("autentificare/", views.LoginView.as_view(), name="login"),
    path("deconectare/", views.LogoutView.as_view(), name="logout"),
    # URLs resetare parolă
    path("resetare-parola/", views.PasswordResetView.as_view(), name="password_reset"),
    path("resetare-parola/trimis/", views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "resetare-parola/confirmare/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("resetare-parola/finalizat/", views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    # URLs autentificare cu doi factori
    path("2fa/configurare/", views.TwoFactorSetupView.as_view(), name="two_factor_setup"),
    path("2fa/verificare/", views.TwoFactorVerifyView.as_view(), name="two_factor_verify"),
    path("2fa/dezactivare/", views.TwoFactorDisableView.as_view(), name="two_factor_disable"),
    path("2fa/coduri-rezerva/", views.TwoFactorBackupCodesView.as_view(), name="two_factor_backup_codes"),
    # Gestionare profil
    path("profil/", views.ProfileView.as_view(), name="profile"),
    path("profil/editare/", views.EditProfileView.as_view(), name="edit_profile"),
    # Director meșteri - SLUG-based URLs
    path("mester/<slug:slug>/", views.CraftsmanDetailView.as_view(), name="craftsman_detail"),
    path("mesterii/", views.CraftsmenListView.as_view(), name="craftsmen_list"),
    # Gestionare portofoliu
    path("portofoliu/", views.CraftsmanPortfolioView.as_view(), name="portfolio"),
    path("portofoliu/gestionare/", views.ManagePortfolioView.as_view(), name="manage_portfolio"),
    path("portofoliu/incarcare/", views.PortfolioUploadView.as_view(), name="portfolio_upload"),
    path("portofoliu/incarcare-multipla/", views.BulkPortfolioUploadView.as_view(), name="bulk_portfolio_upload"),
    path("portofoliu/stergere/<int:pk>/", views.PortfolioDeleteView.as_view(), name="portfolio_delete"),
    # Integrare
    path("integrare/", views.CraftsmanOnboardingView.as_view(), name="onboarding"),
    # Endpoint-uri validare AJAX
    path("api/validare-email/", views.validate_email_ajax, name="validate_email_ajax"),
    path("api/validare-telefon/", views.validate_phone_ajax, name="validate_phone_ajax"),
    # Confirmare email
    path("inregistrare-finalizata/", views.RegistrationCompleteView.as_view(), name="registration_complete"),
    path("confirmare-email/<uidb64>/<token>/", views.confirm_email, name="confirm_email"),
]
