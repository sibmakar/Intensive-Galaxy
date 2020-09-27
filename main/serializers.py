from rest_framework import serializers

from main.models import OrderLine, Order


class OrderLineSerializer(serializers.HyperlinkedModelSerializer):
    product = serializers.StringRelatedField()

    class Meta:
        model = OrderLine
        fields = ("id", "order", "product", "status")
        read_only_fields = ("id", "order", "product")


class OrderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Order
        fields = (
            "shipping_name",
            "shipping_address1",
            "shipping_address2",
            "shipping_pin_code",
            "shipping_city",
            "shipping_country",
            "date_updated",
            "date_added",
        )
