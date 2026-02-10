from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.http import Http404

from .models import Feedback
from orders.models import Order
from payments.models import Payment

class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    fields = ['rating', 'comment']
    template_name = 'feedback/submit_feedback.html'
    success_url = reverse_lazy('order-status')

    def dispatch(self, request, *args, **kwargs):
        """
        Security checks before allowing feedback
        """
        self.order = get_object_or_404(
            Order,
            id=self.kwargs['order_id'],
            user=request.user
        )

        # ❌ Allow feedback only after successful payment
        if not Payment.objects.filter(order=self.order, is_success=True).exists():
            raise Http404("Payment not completed")

        # ❌ Prevent duplicate feedback
        if Feedback.objects.filter(order=self.order).exists():
            raise Http404("Feedback already submitted")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.order = self.order
        return super().form_valid(form)
