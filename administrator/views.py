from django.shortcuts import render



from django.views.generic import TemplateView
from accounts.mixins import RoleRequiredMixin

class AdminDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = ['admin']
    template_name = 'admin/dashboard.html'

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.utils.timezone import now
from datetime import timedelta

from accounts.mixins import RoleRequiredMixin
from orders.models import Order
from payments.models import Payment
from feedback.models import Feedback


class AdminAnalyticsView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "administrator/analytics.html"
    allowed_roles = ["admin"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Time range (last 7 days)
        last_7_days = now() - timedelta(days=7)

        # Orders
        context["total_orders"] = Order.objects.count()
        context["pending_orders"] = Order.objects.filter(status="PENDING").count()
        context["preparing_orders"] = Order.objects.filter(status="PREPARING").count()
        context["completed_orders"] = Order.objects.filter(status="COMPLETED").count()

        # Revenue
        context["total_revenue"] = (
            Payment.objects.filter(is_paid=True)
            .aggregate(total=Sum("amount"))["total"] or 0
        )

        context["weekly_revenue"] = (
            Payment.objects.filter(is_paid=True, created_at__gte=last_7_days)
            .aggregate(total=Sum("amount"))["total"] or 0
        )

        # Feedback
        context["total_feedbacks"] = Feedback.objects.count()

        # Orders per day (for charts)
        context["orders_by_day"] = (
            Order.objects.filter(created_at__gte=last_7_days)
            .values("created_at__date")
            .annotate(count=Count("id"))
            .order_by("created_at__date")
        )

        return context
