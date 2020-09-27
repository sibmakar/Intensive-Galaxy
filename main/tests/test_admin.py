from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from main.models import User
from main.tests import factories


class TestAdminViews(TestCase):
    def test_most_bought_products(self):
        products = [
            factories.ProductFactory(name="A", active=True),
            factories.ProductFactory(name="B", active=True),
            factories.ProductFactory(name="C", active=True),
        ]

        orders = factories.OrderFactory.create_batch(3)
        factories.OrderLineFactory.create_batch(2, order=orders[0], product=products[0])
        factories.OrderLineFactory.create_batch(2, order=orders[0], product=products[1])
        factories.OrderLineFactory.create_batch(2, order=orders[1], product=products[0])
        factories.OrderLineFactory.create_batch(2, order=orders[1], product=products[2])
        factories.OrderLineFactory.create_batch(2, order=orders[2], product=products[0])
        factories.OrderLineFactory.create_batch(1, order=orders[2], product=products[1])
        user = User.objects.create_superuser("user2", "pw432joij")
        self.client.force_login(user)

        response = self.client.post(
            reverse("admin:most-bought-products"),
            {"period": "90"},
        )

        self.assertEqual(200, response.status_code)

        data = dict(zip(response.context["labels"], response.context["values"]))

        self.assertEqual(data, {"B": 3, "C": 2, "A": 6})

    def test_invoice_renders_exactly_as_expected(self):
        # TODO: test case failing
        products = [
            factories.ProductFactory(
                name="The cathedral and the bazaar",
                active=True,
                price=Decimal("500.00"),
            ),
            factories.ProductFactory(
                name="The cathedral and the bazaar",
                active=True,
                price=Decimal("500.00"),
            ),
        ]

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = datetime(2020, 9, 27, 12, 00, 00)

            order = factories.OrderFactory(
                id=1,
                billing_name="sumit",
                billing_address1="new",
                billing_address2="new",
                billing_pin_code="201306",
                billing_city="noida",
                billing_country="in",
            )

            factories.OrderLineFactory.create_batch(1, order=order, product=products[0])
            factories.OrderLineFactory.create_batch(1, order=order, product=products[1])
            user = User.objects.create_superuser("user2", "pw432joij")
            self.client.force_login(user)
            response = self.client.get(
                reverse("admin:invoice", kwargs={"order_id": order.id})
            )

            self.assertEqual(response.status_code, 200)

            pdf_response = self.client.get(
                reverse("admin:invoice", kwargs={"order_id": order.id}),
                {"format": "pdf"},
            )
            content = pdf_response.content
            with open("main/fixtures/invoice.pdf", "rb") as fixture:
                expected_content = fixture.read()
            self.assertEqual(content, expected_content)
