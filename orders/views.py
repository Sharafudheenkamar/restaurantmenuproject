from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from .models import Order

class PlaceOrderView(CreateView):
    model = Order
    fields = ['table']
    success_url = reverse_lazy('order-status')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class OrderStatusView(ListView):
    model = Order
    template_name = 'user/order_status.html'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
from django.http import JsonResponse
from django.views import View
from .models import Order

class OrderStatusAPI(View):
    def get(self, request, order_id):
        order = Order.objects.get(id=order_id)
        return JsonResponse({'status': order.status})

from django.views.generic import ListView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from webpush import send_user_notification

from accounts.mixins import RoleRequiredMixin
from .models import Order
class KitchenOrderListView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    ListView
):
    allowed_roles = ['kitchen']
    model = Order
    template_name = 'kitchen/orders.html'
    context_object_name = 'orders'
    ordering = ['created_at']

    def get_queryset(self):
        return Order.objects.exclude(status='served')
class UpdateOrderStatusView(
    LoginRequiredMixin,
    RoleRequiredMixin,
    UpdateView
):
    allowed_roles = ['kitchen']
    model = Order
    fields = ['status']
    template_name = 'kitchen/update_order.html'
    success_url = reverse_lazy('kitchen-orders')

    def form_valid(self, form):
        response = super().form_valid(form)

        # 🔥 WebSocket real-time update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"order_{self.object.id}",
            {
                'type': 'order_status_update',
                'status': self.object.status
            }
        )

        # 🔔 Push notification when READY
        if self.object.status == 'ready':
            payload = {
                "title": "🍽️ Order Ready!",
                "body": f"Your order for Table {self.object.table.table_number} is ready."
            }

            send_user_notification(
                user=self.object.user,
                payload=payload,
                ttl=1000
            )

        return response
