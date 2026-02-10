from django.views.generic import ListView, UpdateView
from orders.models import Order

class KitchenOrderListView(RoleRequiredMixin, ListView):
    allowed_roles = ['kitchen']
    model = Order
    template_name = 'kitchen/orders.html'


class UpdateOrderStatusView(UpdateView):
    model = Order
    fields = ['status']
    success_url = reverse_lazy('kitchen-orders')
