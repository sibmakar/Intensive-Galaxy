from django.db import models
from django.utils.translation import gettext_lazy as _

from main.managers import ActiveManager, ProductTagManager


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-
    updating ``created`` and ``modified`` fields.
    """

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


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
