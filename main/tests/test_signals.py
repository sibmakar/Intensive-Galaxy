from django.contrib import auth
from django.test import TestCase
from django.urls import reverse

from main import models
from django.core.files.images import ImageFile
from decimal import Decimal


class TestSignal(TestCase):
    def test_thumbnails_are_generated_on_product_save(self):
        product = models.Product(name="Harry Potter", price=Decimal("10.00"))
        product.save()

        with open("main/fixtures/sample-images/harry-potter.jpg", "rb") as f:
            image = models.ProductImage(
                product=product, image=ImageFile(f, name="hp.jpg")
            )
            with self.assertLogs("main", level="INFO") as cm:
                image.save()

        self.assertGreaterEqual(len(cm.output), 1)
        image.thumbnail.delete(save=False)
        image.image.delete(save=False)

    def test_add_to_basket_login_merge_works(self):
        user1 = models.User.objects.create_user("user1@a.com", "pw432joij")
        cb = models.Product.objects.create(
            name="The cathedral and the bazaar",
            slug="cathedral-bazaar",
            price=Decimal("10.00"),
        )
        w = models.Product.objects.create(
            name="Microsoft Windows guide",
            slug="microsoft-windows-guide",
            price=Decimal("12.00"),
        )
        cart = models.Cart.objects.create(user=user1)
        models.ProductInCart.objects.create(cart=cart, product=cb, quantity=2)
        response = self.client.get(reverse("add_to_cart"), {"product_id": w.id})
        response = self.client.post(
            reverse("login"), {"email": "user1@a.com", "password": "pw432joij"},
        )
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        self.assertTrue(models.Cart.objects.filter(user=user1).exists())
        basket = models.Cart.objects.get(user=user1)
        self.assertEquals(basket.count(), 3)
