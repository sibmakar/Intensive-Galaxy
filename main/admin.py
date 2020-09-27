import logging
import tempfile
from datetime import datetime, timedelta

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.forms import forms, TypedChoiceField
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from weasyprint import HTML

from .models import (
    Product,
    ProductImage,
    ProductTag,
    User,
    ProductInCart,
    Cart,
    OrderLine,
    Order,
    Address,
)

logger = logging.getLogger(__name__)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "in_stock", "price")
    list_filter = ("active", "in_stock", "date_updated")
    list_editable = ("in_stock",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("tags",)

    # Slug is an important field for our site, it is used in
    # all the product URLs. We want to limit the ability to
    # change this only by owners of the company
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return list(self.readonly_fields) + ["slug", "name"]

    # This is required for get_readonly_fields to work
    def get_prepopulated_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.prepopulated_fields
        else:
            return {}


class DispatchersProductAdmin(ProductAdmin):
    readonly_fields = ("description", "price", "tags", "active")
    prepopulated_fields = {}
    autocomplete_fields = ()


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    list_filter = ("active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    # tag slugs also appear in urls, therefore it is a
    # property only owners can change
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return list(self.readonly_fields) + ["slug", "name"]

    def get_prepopulated_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.prepopulated_fields
        else:
            return {}


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("thumbnail_tag", "product_name")
    readonly_fields = ("thumbnail",)
    search_fields = ("product__name",)

    # this function returns HTML for the first column defined
    # in the list_display property above
    def thumbnail_tag(self, obj):
        if obj.thumbnail:
            return format_html('<img src="%s"/>' % obj.thumbnail.url)
        return "-"

    # this defines the column name for the list_display
    thumbnail_tag.short_description = "Thumbnail"

    def product_name(self, obj):
        return obj.product.name


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    list_display = ("email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)


class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "name",
        "address1",
        "address2",
        "city",
        "country",
    )
    readonly_fields = ("user",)


class ProductInCartInline(admin.TabularInline):
    model = ProductInCart
    raw_id_fields = ("product",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "count")
    list_editable = ("status",)
    list_filter = ("status",)
    inlines = (ProductInCartInline,)


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    raw_id_fields = ("product",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status")
    list_editable = ("status",)
    list_filter = ("status", "shipping_country", "date_created")
    inlines = (OrderLineInline,)
    fieldsets = (
        (None, {"fields": ("user", "status")}),
        (
            "Billing info",
            {
                "fields": (
                    "billing_name",
                    "billing_address1",
                    "billing_address2",
                    "billing_pin_code",
                    "billing_city",
                    "billing_country",
                )
            },
        ),
        (
            "Shipping info",
            {
                "fields": (
                    "shipping_name",
                    "shipping_address1",
                    "shipping_address2",
                    "shipping_pin_code",
                    "shipping_city",
                    "shipping_country",
                )
            },
        ),
    )


# Employees need a custom version of the order views because
# they are not allowed to change products already purchased
# without adding and removing lines
class CentralOfficeOrderLineInline(admin.TabularInline):
    model = OrderLine
    readonly_fields = ("product",)


class CentralOfficeOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status")
    list_editable = ("status",)
    readonly_fields = ("user",)
    list_filter = ("status", "shipping_country", "date_created")
    inlines = (CentralOfficeOrderLineInline,)
    fieldsets = (
        (None, {"fields": ("user", "status")}),
        (
            "Billing info",
            {
                "fields": (
                    "billing_name",
                    "billing_address1",
                    "billing_address2",
                    "billing_pin_code",
                    "billing_city",
                    "billing_country",
                )
            },
        ),
        (
            "Shipping info",
            {
                "fields": (
                    "shipping_name",
                    "shipping_address1",
                    "shipping_address2",
                    "shipping_pin_code",
                    "shipping_city",
                    "shipping_country",
                )
            },
        ),
    )


# Dispatchers do not need to see the billing address in the fields
class DispatchersOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "shipping_name",
        "date_created",
        "status",
    )
    list_filter = ("status", "shipping_country", "date_created")
    inlines = (CentralOfficeOrderLineInline,)
    fieldsets = (
        (
            "Shipping info",
            {
                "fields": (
                    "shipping_name",
                    "shipping_address1",
                    "shipping_address2",
                    "shipping_pin_code",
                    "shipping_city",
                    "shipping_country",
                )
            },
        ),
    )

    # Dispatchers are only allowed to see orders that
    # are ready to be shipped
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=Order.PAID)


# The class below will pass to the django admin templates a couple
# of extra values that represent colors of headings
class ColoredAdminSite(admin.sites.AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        context["site_header_color"] = getattr(self, "site_header_color", None)
        context["module_caption_color"] = getattr(self, "module_caption_color", None)
        return context


class ReportingColoredAdminSite(ColoredAdminSite):
    def get_urls(self):
        urls = super(ReportingColoredAdminSite, self).get_urls()
        my_urls = [
            path(
                "orders_per_day/",
                self.admin_view(self.orders_per_day),
                name="orders-per-day",
            ),
            path(
                "most_bought_products/",
                self.admin_view(self.most_bought_products),
                name="most-bought-products",
            ),
        ]
        return my_urls + urls

    def orders_per_day(self, request):
        starting_day = datetime.now() - timedelta(days=180)
        order_data = (
            Order.objects.filter(date_created__gt=starting_day)
            .annotate(day=TruncDay("date_created"))
            .values("day")
            .annotate(c=Count("id"))
        )
        labels = [x["day"].strftime("%Y-%m-%d") for x in order_data]
        values = [x["c"] for x in order_data]

        context = dict(
            self.each_context(request),
            title="Orders Per Day",
            labels=labels,
            values=values,
        )

        return TemplateResponse(request, "orders_per_day.html", context)

    def most_bought_products(self, request):
        if request.method == "POST":
            form = PeriodSelectForm(request.POST)
            if form.is_valid():
                days = form.cleaned_data["period"]
                starting_day = datetime.now() - timedelta(days=days)
                data = (
                    OrderLine.objects.filter(order__date_created__gt=starting_day)
                    .values("product__name")
                    .annotate(c=Count("id"))
                )
                logger.info("most_bought_products query: %s", data.query)
                labels = [x["product__name"] for x in data]
                values = [x["c"] for x in data]
        else:
            form = PeriodSelectForm()
            labels = None
            values = None
        context = dict(
            self.each_context(request),
            title="Most bought products",
            form=form,
            labels=labels,
            values=values,
        )

        return TemplateResponse(request, "most_bought_products.html", context)

    def index(self, request, extra_context=None):
        reporting_pages = [
            {"name": "Orders Per Day", "link": "orders_per_day/"},
            {"name": "Most bought products", "link": "most_bought_products/"},
        ]
        if not extra_context:
            extra_context = {}
        extra_context = {"reporting_pages": reporting_pages}
        return super(ReportingColoredAdminSite, self).index(request, extra_context)


# This mixin will be used for the invoice functionality, which is
# only available to owners and employees, but not dispatchers
class InvoiceMixin:
    def get_urls(self):
        urls = super(InvoiceMixin, self).get_urls()
        my_urls = [
            path(
                "invoice/<int:order_id>/",
                self.admin_view(self.invoice_for_order),
                name="invoice",
            )
        ]

        return my_urls + urls

    def invoice_for_order(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)

        if request.GET.get("format") == "pdf":
            html_string = render_to_string("invoice.html", {"order": order})
            html = HTML(string=html_string, base_url=request.build_absolute_uri())

            result = html.write_pdf()

            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = "inline; filename=invoice.pdf"
            response["Content-Transfer-Encoding"] = "binary"

            with tempfile.NamedTemporaryFile(delete=True) as output:
                output.write(result)
                output.flush()
                output = open(output.name, "rb")
                binary_pdf = output.read()
                response.write(binary_pdf)
            return response

        return render(request, "invoice.html", {"order": order})


# Finally we define 3 instances of AdminSite, each with their own
# set of required permissions and colors
class OwnersAdminSite(InvoiceMixin, ReportingColoredAdminSite):
    site_header = "Intensive Galaxy Owners Administration"
    site_header_color = "black"
    module_caption_color = "grey"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser


class CentralOfficeAdminSite(InvoiceMixin, ReportingColoredAdminSite):
    site_header = "Intensive Galaxy Central Office Administration"
    site_header_color = "purple"
    module_caption_color = "pink"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_employee


class DispatchersAdminSite(ColoredAdminSite):
    site_header = "Intensive Galaxy Dispatch Administration"
    site_header_color = "green"
    module_caption_color = "lightgreen"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_dispatcher


class PeriodSelectForm(forms.Form):
    PERIODS = ((30, "30 Days"), (60, "60 Days"), (90, "90 Days"))
    period = TypedChoiceField(choices=PERIODS, coerce=int, required=True)


main_admin = OwnersAdminSite()
main_admin.register(Product, ProductAdmin)
main_admin.register(ProductTag, ProductTagAdmin)
main_admin.register(ProductImage, ProductImageAdmin)
main_admin.register(User, UserAdmin)
main_admin.register(Address, AddressAdmin)
main_admin.register(Cart, CartAdmin)
main_admin.register(Order, OrderAdmin)
central_office_admin = CentralOfficeAdminSite("central-office-admin")
central_office_admin.register(Product, ProductAdmin)
central_office_admin.register(ProductTag, ProductTagAdmin)
central_office_admin.register(ProductImage, ProductImageAdmin)
central_office_admin.register(Address, AddressAdmin)
central_office_admin.register(Order, CentralOfficeOrderAdmin)
dispatchers_admin = DispatchersAdminSite("dispatchers-admin")
dispatchers_admin.register(Product, DispatchersProductAdmin)
dispatchers_admin.register(ProductTag, ProductTagAdmin)
dispatchers_admin.register(Order, DispatchersOrderAdmin)
