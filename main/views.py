import logging
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    FormView,
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.shortcuts import get_object_or_404, render

from .forms import UserCreationForm, CartLineFormSet
from .models import Product, ProductTag, Address, Cart, ProductInCart
from . import forms

logger = logging.getLogger(__name__)


class SignUpView(FormView):
    template_name = "signup.html"
    form_class = UserCreationForm

    def get_success_url(self):
        success_url = self.request.GET.get("next", "/")
        return success_url

    def form_valid(self, form):
        response = super(SignUpView, self).form_valid(form)
        form.save()
        email = form.cleaned_data.get("email")
        raw_password = form.cleaned_data.get("password1")
        logger.info("New signup for email=%s through SignupView", email)
        user = authenticate(email=email, password=raw_password)
        login(self.request, user)
        form.send_mail()
        messages.info(self.request, "You signed up successfully.")
        return response


class ContactUsView(FormView):
    template_name = "contact_form.html"
    form_class = forms.ContactForm
    success_url = "/"

    def form_valid(self, form):
        form.send_mail()
        return super(ContactUsView, self).form_valid(form)


class ProductListView(ListView):
    """Product List View

    Notes
    -----
    Lists products
    """

    template_name = "product_list.html"
    paginate_by = 4

    def get_queryset(self):
        tag = self.kwargs["tag"]
        self.tag = None
        if tag != "all":
            self.tag = get_object_or_404(ProductTag, slug=tag)
        if self.tag:
            products = Product.objects.active().filter(tags=self.tag)
        else:
            products = Product.objects.active()
        return products.order_by("name")


class ProductDetailView(DetailView):
    template_name = "product_detail.html"
    model = Product


class AddressListView(LoginRequiredMixin, ListView):
    model = Address
    template_name = "address_list.html"

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class AddressCreateView(LoginRequiredMixin, CreateView):
    model = Address
    template_name = "address_form.html"
    fields = ["name", "address1", "address2", "pin_code", "city", "country"]
    success_url = reverse_lazy("address_list")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return super(AddressCreateView, self).form_valid(form)


class AddressUpdateView(LoginRequiredMixin, UpdateView):
    model = Address
    template_name = "address_update.html"
    fields = ["name", "address1", "address2", "pin_code", "city", "country"]
    success_url = reverse_lazy("address_list")

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class AddressDeleteView(LoginRequiredMixin, DeleteView):
    model = Address
    template_name = "address_confirm_delete.html"
    success_url = reverse_lazy("address_list")

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


def add_to_cart(request):
    """
    Method to add products to the cart

    Parameters
    ----------
    request

    Returns
    -------

    """
    product = get_object_or_404(Product, pk=request.GET.get("product_id"))
    cart = request.cart
    if not request.cart:
        if request.user.is_authenticated:
            user = request.user
        else:
            user = None
        cart = Cart.objects.create(user=user)
        request.session["cart_id"] = cart.id
    cart_in_product, created = ProductInCart.objects.get_or_create(
        cart=cart, product=product
    )
    if not created:
        cart_in_product.quantity += 1
        cart_in_product.save()
    return HttpResponseRedirect(reverse("product", args=(product.slug,)))


def manage_cart(request):
    """
    This view manages the cart
    """
    if not request.cart:
        return render(request, "cart.html", {"formset": None})

    if request.method == "POST":
        formset = CartLineFormSet(request.POST, instance=request.cart)
        if formset.is_valid():
            formset.save()
    else:
        formset = CartLineFormSet(instance=request.cart)
    if request.cart.is_empty():
        return render(request, "cart.html", {"formset": None})

    return render(request, "cart.html", {"formset": formset})
