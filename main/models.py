from django.contrib.auth.models import AbstractUser
from django.core import exceptions
from django.core.exceptions import ValidationError
from django.core.handlers import exception
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from main.managers import ActiveManager, ProductTagManager, UserManager

import logging

logger = logging.getLogger(__name__)


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-
    updating ``created`` and ``modified`` fields.
    """

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    username = None
    email = models.EmailField("email address", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()


class ProductTag(TimeStampedModel):
    """Product Tag Model"""

    name = models.CharField(max_length=32)
    slug = models.SlugField(max_length=48)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    objects = ProductTagManager()

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.slug

    class Meta:
        verbose_name = _("Product Tag")
        verbose_name_plural = _("Product Tags")


class Product(TimeStampedModel):
    """Product Model"""

    name = models.CharField(max_length=32)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    tags = models.ManyToManyField(to=ProductTag, blank=True)
    slug = models.SlugField(max_length=48)
    active = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)

    objects = ActiveManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")


class ProductImage(TimeStampedModel):
    """Product Image Model"""

    product = models.ForeignKey(to=Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="product-images")
    thumbnail = models.ImageField(upload_to="product-thumbnails", null=True)

    def __str__(self):
        return f"{self.product.id} + | + {self.product.name}"

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")


class Address(TimeStampedModel):
    SUPPORTED_COUNTRIES = (
        ("in", "India"),
        ("en", "England"),
        ("us", "United States of America"),
    )
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    name = models.CharField(max_length=60)
    address1 = models.CharField(verbose_name=_("Address Line 1"), max_length=60)
    address2 = models.CharField(
        verbose_name=_("Address Line 2"), max_length=60, blank=True
    )
    pin_code = models.CharField(verbose_name=_("ZIP / Postal Code"), max_length=12)
    city = models.CharField(max_length=60)
    country = models.CharField(max_length=3, choices=SUPPORTED_COUNTRIES)

    def __str__(self):
        return ", ".join(
            [
                self.name,
                self.address1,
                self.address2,
                self.pin_code,
                self.city,
                self.country,
            ]
        )


class Cart(TimeStampedModel):
    OPEN = 10
    SUBMITTED = 20
    STATUSES = ((OPEN, "Open"), (SUBMITTED, "Submitted"))

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True)
    status = models.IntegerField(choices=STATUSES, default=OPEN)

    def is_empty(self):
        return self.productincart_set.all().count() == 0

    def count(self):
        return sum(i.quantity for i in self.productincart_set.all())

    def create_order(self, billing_address, shipping_address):
        if not self.user:
            raise ValidationError("Cannot create order without user")

        logger.info(
            "Creating Order for basket_id=%d"
            ", shipping_address_id=%d, billing_address_id=%d",
            self.id,
            shipping_address.id,
            billing_address.id,
        )
        order_data = {
            "user": self.user,
            "billing_name": billing_address.name,
            "billing_address1": billing_address.address1,
            "billing_address2": billing_address.address2,
            "billing_pin_code": billing_address.pin_code,
            "billing_city": billing_address.city,
            "billing_country": billing_address.country,
            "shipping_name": shipping_address.name,
            "shipping_address1": shipping_address.address1,
            "shipping_address2": shipping_address.address2,
            "shipping_pin_code": shipping_address.pin_code,
            "shipping_city": shipping_address.city,
            "shipping_country": shipping_address.country,
        }
        order = Order.objects.create(**order_data)
        c = 0
        for product in self.productincart_set.all():
            for item in range(product.quantity):
                order_line_data = {"order": order, "product": product.product}
                order_line = OrderLine.objects.create(**order_line_data)
                c += 1
            logger.info("Created order with id=%d and lines_count=%d", order.id, c)
        self.status = Cart.SUBMITTED
        self.save()
        return order

    def __str__(self):
        return f"{self.user.first_name}'s Cart"


class ProductInCart(TimeStampedModel):
    cart = models.ForeignKey(to=Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(to=Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])


class Order(TimeStampedModel):
    """Order Model"""

    NEW = 10
    PAID = 20
    DONE = 30
    STATUSES = ((NEW, "New"), (PAID, "Paid"), (DONE, "Done"))

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.IntegerField(choices=STATUSES, default=NEW)
    billing_name = models.CharField(max_length=60)
    billing_address1 = models.CharField(max_length=60)
    billing_address2 = models.CharField(max_length=60, blank=True)
    billing_pin_code = models.CharField(max_length=12)
    billing_city = models.CharField(max_length=60)
    billing_country = models.CharField(max_length=3)
    shipping_name = models.CharField(max_length=60)
    shipping_address1 = models.CharField(max_length=60)
    shipping_address2 = models.CharField(max_length=60, blank=True)
    shipping_pin_code = models.CharField(max_length=12)
    shipping_city = models.CharField(max_length=60)
    shipping_country = models.CharField(max_length=3)

    def __str__(self):
        return f"{self.user.first_name}'s Order"


class OrderLine(TimeStampedModel):
    """Order Line Model"""

    NEW = 10
    PROCESSING = 20
    SENT = 30
    CANCELLED = 40
    STATUSES = (
        (NEW, "New"),
        (PROCESSING, "Processing"),
        (SENT, "Sent"),
        (CANCELLED, "Cancelled"),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    status = models.IntegerField(choices=STATUSES, default=NEW)
