from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework import routers

from main import forms, api
from . import views

router = routers.DefaultRouter()
router.register(r"orderlines", api.PaidOrderLineViewSet)
router.register(r"orders", api.PaidOrderViewSet)

urlpatterns = [
    path(
        "about-us/",
        TemplateView.as_view(template_name="about_us.html"),
        name="about_us",
    ),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("contact-us/", views.ContactUsView.as_view(), name="contact_us"),
    path("products/<slug:tag>/", views.ProductListView.as_view(), name="products-list"),
    path(
        "product/<slug:slug>/",
        # DetailView.as_view(model=models.Product),
        views.ProductDetailView.as_view(),
        name="product",
    ),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html", form_class=forms.AuthenticationForm
        ),
        name="login",
    ),
    path("address/", views.AddressListView.as_view(), name="address_list"),
    path("address/create/", views.AddressCreateView.as_view(), name="address_create"),
    path("address/<int:pk>/", views.AddressUpdateView.as_view(), name="address_update"),
    path(
        "address/<int:pk>/delete/",
        views.AddressDeleteView.as_view(),
        name="address_delete",
    ),
    path("add_to_cart/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.manage_cart, name="cart"),
    path(
        "order/done/",
        TemplateView.as_view(template_name="order_done.html"),
        name="checkout_done",
    ),
    path(
        "order/address_select/",
        views.AddressSelectionView.as_view(),
        name="address_select",
    ),
    path("api/", include(router.urls)),
    path("customer-service/<int:order_id>/", views.room, name="cs_chat"),
]
