"""
URL patterns for messaging app
"""
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Conversații
    path('', views.ConversationListView.as_view(), name='conversation_list'),
    path('conversation/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    
    # Trimitere mesaje
    path('contact/<int:craftsman_id>/', views.send_contact_message, name='send_contact_message'),
    path('reply/<int:conversation_id>/', views.send_reply, name='send_reply'),
    
    # AJAX endpoints
    path('mark-read/<int:conversation_id>/', views.mark_conversation_read, name='mark_conversation_read'),
    path('unread-count/', views.get_unread_count, name='get_unread_count'),
]
