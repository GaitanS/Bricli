from django.urls import include, path
from django.views.generic import RedirectView

from . import views

app_name = "services"

urlpatterns = [
    # Legacy URL redirect: /servicii/comenzi/ -> redirect based on user type
    path("comenzi/", views.OrdersRedirectView.as_view(), name="orders_redirect"),

    path("categorii/", views.ServiceCategoryListView.as_view(), name="categories"),
    path("cautare/", views.ServiceSearchView.as_view(), name="search"),
    path("categorii/<slug:slug>/", views.ServiceCategoryDetailView.as_view(), name="category_detail"),
    path("comanda/creare/", views.CreateOrderView.as_view(), name="create_order"),
    path("comanda/<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("comanda/<int:pk>/editare/", views.EditOrderView.as_view(), name="edit_order"),
    path("comanda/<int:pk>/stergere/", views.DeleteOrderView.as_view(), name="delete_order"),
    path("comanda/<int:pk>/publicare/", views.PublishOrderView.as_view(), name="publish_order"),
    path("comenzile-mele/", views.MyOrdersView.as_view(), name="my_orders"),
    path("ofertele-mele/", views.MyQuotesView.as_view(), name="my_quotes"),
    path("comenzi-disponibile/", views.AvailableOrdersView.as_view(), name="available_orders"),
    path("oferta/<int:pk>/acceptare/", views.AcceptQuoteView.as_view(), name="accept_quote"),
    path("oferta/<int:pk>/refuzare/", views.RejectQuoteView.as_view(), name="reject_quote"),
    path("comanda/<int:pk>/confirmare/", views.ConfirmOrderView.as_view(), name="confirm_order"),
    path("comanda/<int:pk>/refuzare/", views.DeclineOrderView.as_view(), name="decline_order"),
    path("comanda/<int:pk>/finalizare/", views.CompleteOrderView.as_view(), name="complete_order"),
    path("comanda/<int:order_pk>/oferta/", views.CreateQuoteView.as_view(), name="create_quote"),
    path("comanda/<int:pk>/recenzie/", views.CreateReviewView.as_view(), name="create_review"),
    path("recenzie/<int:pk>/", views.ReviewDetailView.as_view(), name="review_detail"),
    path("recenzie/<int:pk>/editare/", views.EditReviewView.as_view(), name="edit_review"),
    path("mester/<int:pk>/recenzii/", views.CraftsmanReviewsView.as_view(), name="craftsman_reviews"),
    path(
        "recenzie/<int:review_pk>/incarcare-imagine/", views.ReviewImageUploadView.as_view(), name="upload_review_image"
    ),
    # URLs sistem lead (stil MyBuilder)
    path("comanda/<int:pk>/invitare/", views.InviteCraftsmenView.as_view(), name="invite_craftsmen"),
    path(
        "comanda/<int:pk>/lista-scurta/<int:craftsman_id>/",
        views.ShortlistCraftsmanView.as_view(),
        name="shortlist_craftsman",
    ),
    path("comanda/<int:pk>/invitatie/acceptare/", views.AcceptInvitationView.as_view(), name="accept_invitation"),
    path("comanda/<int:pk>/invitatie/refuzare/", views.DeclineInvitationView.as_view(), name="decline_invitation"),
    # REMOVED: Wallet URL - wallet system removed in Phase 2
    # path("portofel/", views.WalletView.as_view(), name="wallet"),
    # URLs gestionare servicii meșter
    path("serviciile-mele/", views.CraftsmanServicesView.as_view(), name="craftsman_services"),
    path("serviciile-mele/adaugare/", views.AddCraftsmanServiceView.as_view(), name="add_craftsman_service"),
    path("serviciile-mele/<int:pk>/editare/", views.EditCraftsmanServiceView.as_view(), name="edit_craftsman_service"),
    path(
        "serviciile-mele/<int:pk>/stergere/",
        views.DeleteCraftsmanServiceView.as_view(),
        name="delete_craftsman_service",
    ),
    # Notificări
    path("notificari/", views.NotificationsView.as_view(), name="notifications"),
    # Dashboard Meșter
    path("dashboard/", views.CraftsmanDashboardView.as_view(), name="craftsman_dashboard"),
    # REMOVED: Payment system URLs - wallet system removed in Phase 2
    # TODO Phase 3: Replace with subscription payment URLs
    # path("plati/", include("services.payment_urls")),
]
