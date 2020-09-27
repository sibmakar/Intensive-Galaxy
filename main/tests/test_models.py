from decimal import Decimal
from django.test import TestCase
from main import models
from main.tests.factories import ProductFactory, UserFactory, AddressFactory


class TestProduct(TestCase):
    def test_active_manager_works(self):
        ProductFactory.create_batch(2, active=True)
        ProductFactory(active=False)

        self.assertEqual(len(models.Product.objects.active()), 2)


class TestCart(TestCase):
    def test_create_order_works(self):
        p1 = ProductFactory()
        p2 = ProductFactory()
        user1 = UserFactory()
        billing = AddressFactory(user=user1)
        shipping = AddressFactory(user=user1)
        cart = models.Cart.objects.create(user=user1)
        models.ProductInCart.objects.create(cart=cart, product=p1)
        models.ProductInCart.objects.create(cart=cart, product=p2)

        with self.assertLogs("main.models", level="INFO") as cm:
            order = cart.create_order(billing, shipping)

        self.assertGreaterEqual(len(cm.output), 1)

        order.refresh_from_db()

        self.assertEqual(order.user, user1)
        self.assertEqual(order.billing_address1, billing.address1)
        self.assertEqual(order.shipping_address1, shipping.address1)

        self.assertEqual(order.lines.all().count(), 2)
        lines = order.lines.all()
        self.assertEqual(lines[0].product, p1)
        self.assertEqual(lines[1].product, p2)
