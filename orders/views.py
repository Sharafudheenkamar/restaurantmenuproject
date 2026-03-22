from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from webpush import send_user_notification

from accounts.mixins import RoleRequiredMixin
from menu.models import Table

from .models import Order


class PlaceOrderView(CreateView):
    model = Order
    fields = ["table"]
    success_url = reverse_lazy("order-status")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class OrderStatusView(ListView):
    model = Order
    template_name = "user/order_status.html"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderStatusAPI(View):
    def get(self, request, order_id):
        order = Order.objects.get(id=order_id)
        return JsonResponse({"status": order.status})


class KitchenOrderListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    allowed_roles = ["kitchen"]
    model = Order
    template_name = "kitchen/orders.html"
    context_object_name = "orders"
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = (
            Order.objects.select_related("user", "table")
            .prefetch_related("items__menu_item")
            .all()
        )

        customer_id = self.request.GET.get("customer")
        table_id = self.request.GET.get("table")

        if customer_id:
            queryset = queryset.filter(user_id=customer_id)

        if table_id:
            queryset = queryset.filter(table_id=table_id)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = context["orders"]
        context["active_orders"] = [o for o in orders if o.status != "served"]
        context["served_orders"] = [o for o in orders if o.status == "served"]

        User = get_user_model()
        context["customers"] = User.objects.filter(role="customer").order_by("username")
        context["tables"] = Table.objects.all().order_by("number")
        context["selected_customer"] = self.request.GET.get("customer", "")
        context["selected_table"] = self.request.GET.get("table", "")
        return context


class UpdateOrderStatusView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    allowed_roles = ["kitchen"]
    model = Order
    fields = ["status"]
    template_name = "kitchen/update_order.html"
    success_url = reverse_lazy("kitchen-orders")

    def form_valid(self, form):
        response = super().form_valid(form)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"order_{self.object.id}",
            {
                "type": "order_status_update",
                "status": self.object.status,
            },
        )

        if self.object.status == "ready":
            payload = {
                "title": "🍽️ Order Ready!",
                "body": f"Your order for Table {self.object.table.number} is ready.",
            }

            send_user_notification(user=self.object.user, payload=payload, ttl=1000)

        return response
