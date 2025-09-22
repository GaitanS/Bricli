from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Simplified registration (MyHammer style)
    path('register/', views.SimpleRegisterView.as_view(), name='register'),
    path('register/craftsman/', views.SimpleCraftsmanRegisterView.as_view(), name='craftsman_register'),
    path('register/simple/', views.SimpleRegisterView.as_view(), name='simple_register'),
    path('register/simple/craftsman/', views.SimpleCraftsmanRegisterView.as_view(), name='simple_craftsman_register'),

    # Full registration forms
    path('register/full/', views.RegisterView.as_view(), name='full_register'),
    path('register/full/craftsman/', views.CraftsmanRegisterView.as_view(), name='full_craftsman_register'),

    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.EditProfileView.as_view(), name='edit_profile'),

    # Craftsmen directory
    path('craftsman/<int:pk>/', views.CraftsmanDetailView.as_view(), name='craftsman_detail'),
    path('craftsmen/', views.CraftsmenListView.as_view(), name='craftsmen_list'),

    # Portfolio management
    path('portfolio/', views.CraftsmanPortfolioView.as_view(), name='portfolio'),
    path('portfolio/upload/', views.PortfolioUploadView.as_view(), name='portfolio_upload'),
    path('portfolio/bulk-upload/', views.BulkPortfolioUploadView.as_view(), name='bulk_portfolio_upload'),
    path('portfolio/delete/<int:pk>/', views.PortfolioDeleteView.as_view(), name='portfolio_delete'),

    # Onboarding
    path('onboarding/', views.CraftsmanOnboardingView.as_view(), name='onboarding'),
]
