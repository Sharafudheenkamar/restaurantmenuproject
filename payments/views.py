from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.db.models import Sum, F
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from orders.models import Order, OrderItem
from .models import Payment

class MakePaymentView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/make_payment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order = get_object_or_404(
            Order,
            id=self.kwargs['order_id'],
            user=self.request.user
        )

        total_amount = (
            OrderItem.objects
            .filter(order=order)
            .aggregate(
                total=Sum(F('quantity') * F('menu_item__price'))
            )['total'] or 0
        )

        context['order'] = order
        context['amount'] = total_amount
        context['order_items'] = order.items.select_related('menu_item').all()
        context['payment'] = Payment.objects.filter(order=order).first()
        return context

    def post(self, request, *args, **kwargs):
        order = get_object_or_404(
            Order,
            id=self.kwargs['order_id'],
            user=request.user
        )

        total_amount = (
            OrderItem.objects
            .filter(order=order)
            .aggregate(
                total=Sum(F('quantity') * F('menu_item__price'))
            )['total'] or 0
        )

        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'amount': total_amount,
                'payment_method': request.POST.get('method', 'UPI'),
                'is_success': True,
            },
        )
        if not created:
            payment.amount = total_amount
            payment.payment_method = request.POST.get('method', payment.payment_method or 'UPI')
            payment.is_success = True
            payment.save(update_fields=['amount', 'payment_method', 'is_success'])

        # 🔄 Update order status
        order.status = 'pending'   # kitchen will start preparing
        order.save()

        # 🔥 Notify kitchen via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "kitchen",
            {
                "type": "new_order",
                "order_id": order.id,
            }
        )

        return redirect('order-status')
