from django.views.generic import FormView, ListView, DetailView
from django.shortcuts import get_object_or_404
from .models import Product, ProductTag
from . import forms


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
