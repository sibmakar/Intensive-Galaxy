from decimal import Decimal
from django.test import TestCase
from main.models import Product


class TestProduct(TestCase):
    def test_active_manager_works(self):
        Product.objects.create(
            name="The cathedral and the bazaar", price=Decimal("10.00")
        )
        Product.objects.create(name="Pride and Prejudice", price=Decimal("2.00"))
        Product.objects.create(
            name="A Tale of Two Cities", price=Decimal("2.00"), active=False
        )
        self.assertEqual(len(Product.objects.active()), 2)
