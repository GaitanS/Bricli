"""
API URLs pentru accounts app
"""
from django.urls import path
from .api_views import CheckUserExistsView, ResendCodeView
from .views import VerifyCodeView

app_name = 'accounts_api'

urlpatterns = [
    path('check-user/', CheckUserExistsView.as_view(), name='check_user_exists'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify_code'),
    path('resend-code/', ResendCodeView.as_view(), name='resend_code'),
]
