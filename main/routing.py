from django.urls import path

from main import consumers

websocket_urlpatterns = [
    path("ws/customer-service/<int:order_id>/", consumers.ChatConsumer)
]
