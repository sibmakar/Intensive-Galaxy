from rest_framework import viewsets

from main.models import OrderLine, Order
from main.serializers import OrderLineSerializer, OrderSerializer


class PaidOrderLineViewSet(viewsets.ModelViewSet):
    queryset = OrderLine.objects.filter(order__status=Order.PAID).order_by(
        "-order__date_created"
    )
    serializer_class = OrderLineSerializer
    filter_fields = ("order", "status")


class PaidOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.filter(status=Order.PAID).order_by("-date_added")
    serializer_class = OrderSerializer
