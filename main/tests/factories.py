from factory import fuzzy, SubFactory
from factory.django import DjangoModelFactory

from main.models import User, Product, Address, OrderLine, Order


class UserFactory(DjangoModelFactory):
    email = "user@site.com"

    class Meta:
        model = User
        django_get_or_create = ("email",)


class ProductFactory(DjangoModelFactory):
    price = fuzzy.FuzzyDecimal(1.0, 1000.0, 2)

    class Meta:
        model = Product


class AddressFactory(DjangoModelFactory):
    class Meta:
        model = Address


class OrderLineFactory(DjangoModelFactory):
    class Meta:
        model = OrderLine


class OrderFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)

    class Meta:
        model = Order
