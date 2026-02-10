from django.urls import path
from .views import (
    PlaceOrderView,
    OrderStatusView,
    OrderStatusAPI,
    KitchenOrderListView,
    UpdateOrderStatusView
)

urlpatterns = [
    # User
    path('place/', PlaceOrderView.as_view(), name='place-order'),
    path('status/', OrderStatusView.as_view(), name='order-status'),

    # AJAX (fallback)
    path('status/<int:order_id>/', OrderStatusAPI.as_view(), name='order-status-api'),

    # Kitchen
    path('kitchen/', KitchenOrderListView.as_view(), name='kitchen-orders'),
    path('kitchen/update/<int:pk>/', UpdateOrderStatusView.as_view(), name='update-order'),
]
