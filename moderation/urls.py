"""
URL patterns for moderation app
"""
from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    # Reporting
    path('report/', views.create_report_view, name='create_report'),
    path('report/form/', views.report_form_modal, name='report_form_modal'),
    path('quick-report/<int:content_type_id>/<int:object_id>/<str:report_type>/', 
         views.quick_report, name='quick_report'),
    path('my-reports/', views.MyReportsView.as_view(), name='my_reports'),
    
    # User blocking
    path('block-user/<int:user_id>/', views.block_user_request, name='block_user_request'),
    
    # Error pages
    path('rate-limited/', views.rate_limited_view, name='rate_limited'),
    path('ip-blocked/', views.ip_blocked_view, name='ip_blocked'),
    path('account-suspended/', views.account_suspended_view, name='account_suspended'),
    path('account-banned/', views.account_banned_view, name='account_banned'),
    
    # Testing (remove in production)
    path('test-rate-limit/', views.test_rate_limit, name='test_rate_limit'),
]
