from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('categories/', views.ServiceCategoryListView.as_view(), name='categories'),
    path('category/<slug:slug>/', views.ServiceCategoryDetailView.as_view(), name='category_detail'),
    path('order/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('order/<int:pk>/edit/', views.EditOrderView.as_view(), name='edit_order'),
    path('order/<int:pk>/publish/', views.PublishOrderView.as_view(), name='publish_order'),
    path('my-orders/', views.MyOrdersView.as_view(), name='my_orders'),
    path('available-orders/', views.AvailableOrdersView.as_view(), name='available_orders'),
    path('quote/<int:pk>/accept/', views.AcceptQuoteView.as_view(), name='accept_quote'),
    path('quote/<int:pk>/reject/', views.RejectQuoteView.as_view(), name='reject_quote'),
    path('order/<int:order_pk>/quote/', views.CreateQuoteView.as_view(), name='create_quote'),
    path('order/<int:pk>/review/', views.CreateReviewView.as_view(), name='create_review'),
    path('review/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('craftsman/<int:pk>/reviews/', views.CraftsmanReviewsView.as_view(), name='craftsman_reviews'),
    path('review/<int:review_pk>/upload-image/', views.ReviewImageUploadView.as_view(), name='upload_review_image'),
]
