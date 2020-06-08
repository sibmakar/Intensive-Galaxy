import logging
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.generic import FormView, ListView, DetailView
from django.shortcuts import get_object_or_404

from .forms import UserCreationForm
from .models import Product, ProductTag
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
