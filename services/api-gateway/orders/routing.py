"""
WebSocket routing for orders.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/orders/(?P<order_id>[0-9a-f-]+)/$', consumers.OrderStatusConsumer.as_asgi()),
]

