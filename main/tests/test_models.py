from decimal import Decimal
from django.test import TestCase
from main import models


class TestProduct(TestCase):
    def test_active_manager_works(self):
        models.Product.objects.create(
            name="The cathedral and the bazaar", price=Decimal("10.00")
        )
        models.Product.objects.create(name="Pride and Prejudice", price=Decimal("2.00"))
        models.Product.objects.create(
            name="A Tale of Two Cities", price=Decimal("2.00"), active=False
        )
        self.assertEqual(len(models.Product.objects.active()), 2)


class TestCart(TestCase):
    def test_create_order_works(self):
        p1 = models.Product.objects.create(
            name="The cathedral and the bazaar",
            price=Decimal("10.00"),
        )
        p2 = models.Product.objects.create(
            name="Pride and Prejudice", price=Decimal("2.00")
        )
        user1 = models.User.objects.create_user("user1", "pw432joij")
        billing = models.Address.objects.create(
            user=user1,
            name="John Kimball",
            address1="127 Strudel road",
            city="London",
            country="uk",
        )
        shipping = models.Address.objects.create(
            user=user1,
            name="John Kimball",
            address1="123 Deacon road",
            city="London",
            country="uk",
        )
        cart = models.Cart.objects.create(user=user1)
        models.ProductInCart.objects.create(cart=cart, product=p1)
        models.ProductInCart.objects.create(cart=cart, product=p2)

        with self.assertLogs("main.models", level="INFO") as cm:
            order = cart.create_order(billing, shipping)

        self.assertGreaterEqual(len(cm.output), 1)

        order.refresh_from_db()

        self.assertEqual(order.user, user1)
        self.assertEqual(order.billing_address1, "127 Strudel road")
        self.assertEqual(order.shipping_address1, "123 Deacon road")

        self.assertEqual(order.lines.all().count(), 2)
        lines = order.lines.all()
        self.assertEqual(lines[0].product, p1)
        self.assertEqual(lines[1].product, p2)
