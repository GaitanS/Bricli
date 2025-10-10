"""
Authentication URLs (mounted at root /)
Namespace: 'auth'
"""

from django.urls import path

from . import views

app_name = "auth"

urlpatterns = [
    # Registration choice and forms
    path("inregistrare/", views.RegistrationChoiceView.as_view(), name="registration_choice"),
    path("inregistrare/client/", views.SimpleRegisterView.as_view(), name="register"),
    # Alias for backward compatibility (old templates may use simple_register)
    path("inregistrare/client/", views.SimpleRegisterView.as_view(), name="simple_register"),
    path("inregistrare/meserias/", views.SimpleCraftsmanRegisterView.as_view(), name="craftsman_register"),
    # Alias for backward compatibility (old templates may use simple_craftsman_register)
    path("inregistrare/meserias/", views.SimpleCraftsmanRegisterView.as_view(), name="simple_craftsman_register"),
    # Login/Logout
    path("autentificare/", views.LoginView.as_view(), name="login"),
    path("deconectare/", views.LogoutView.as_view(), name="logout"),
    # Password reset
    path("resetare-parola/", views.PasswordResetView.as_view(), name="password_reset"),
    path("resetare-parola/trimis/", views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "resetare-parola/confirmare/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("resetare-parola/finalizat/", views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    # 2FA
    path("2fa/configurare/", views.TwoFactorSetupView.as_view(), name="two_factor_setup"),
    path("2fa/verificare/", views.TwoFactorVerifyView.as_view(), name="two_factor_verify"),
    path("2fa/dezactivare/", views.TwoFactorDisableView.as_view(), name="two_factor_disable"),
    path("2fa/coduri-rezerva/", views.TwoFactorBackupCodesView.as_view(), name="two_factor_backup_codes"),
    # Email confirmation
    path("inregistrare-finalizata/", views.RegistrationCompleteView.as_view(), name="registration_complete"),
    path("confirmare-email/<uidb64>/<token>/", views.confirm_email, name="confirm_email"),
]
