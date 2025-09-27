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

    path('quote/<int:pk>/accept/', views.AcceptQuoteView.as_view(), name='accept_quote'),
    path('quote/<int:pk>/reject/', views.RejectQuoteView.as_view(), name='reject_quote'),
    path('order/<int:pk>/confirm/', views.ConfirmOrderView.as_view(), name='confirm_order'),
    path('order/<int:pk>/decline/', views.DeclineOrderView.as_view(), name='decline_order'),
    path('order/<int:order_pk>/quote/', views.CreateQuoteView.as_view(), name='create_quote'),
    path('order/<int:pk>/review/', views.CreateReviewView.as_view(), name='create_review'),
    path('review/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('craftsman/<int:pk>/reviews/', views.CraftsmanReviewsView.as_view(), name='craftsman_reviews'),
    path('review/<int:review_pk>/upload-image/', views.ReviewImageUploadView.as_view(), name='upload_review_image'),

    # MyBuilder-style Lead System URLs
    path('order/<int:pk>/invite/', views.InviteCraftsmenView.as_view(), name='invite_craftsmen'),
    path('order/<int:pk>/shortlist/<int:craftsman_id>/', views.ShortlistCraftsmanView.as_view(), name='shortlist_craftsman'),
    path('wallet/', views.WalletView.as_view(), name='wallet'),

    # Craftsman Services Management URLs
    path('my-services/', views.CraftsmanServicesView.as_view(), name='craftsman_services'),
    path('my-services/add/', views.AddCraftsmanServiceView.as_view(), name='add_craftsman_service'),
    path('my-services/<int:pk>/edit/', views.EditCraftsmanServiceView.as_view(), name='edit_craftsman_service'),
    path('my-services/<int:pk>/delete/', views.DeleteCraftsmanServiceView.as_view(), name='delete_craftsman_service'),
]
