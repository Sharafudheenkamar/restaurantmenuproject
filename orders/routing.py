from django.urls import path
from .consumers import OrderStatusConsumer

websocket_urlpatterns = [
    path('ws/order/<int:order_id>/', OrderStatusConsumer.as_asgi()),
]
