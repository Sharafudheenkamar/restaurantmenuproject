from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from orders.models import Order

from .forms import LoginForm, SignupForm


class SignupView(CreateView):
    form_class = SignupForm
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('login')


class CustomLoginView(LoginView):
    template_name = 'auth/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == "customer":
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user
        next_url = self.request.POST.get("next") or self.request.GET.get("next")

        if user.role == "customer":
            if next_url:
                return next_url
            return reverse_lazy("menu:menu-list")

        if user.role == "admin":
            return reverse_lazy("administrator:admin-dashboard")

        if user.role == "kitchen":
            return reverse_lazy("kitchen-orders")

        return reverse_lazy("login")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'auth/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = (
            Order.objects.filter(user=self.request.user)
            .select_related("table")
            .prefetch_related("items__menu_item")
            .order_by("-created_at")
        )

        order_rows = []
        for order in orders:
            try:
                payment = order.payment
            except ObjectDoesNotExist:
                payment = None
            order_rows.append({"order": order, "payment": payment})

        context["order_rows"] = order_rows
        context["order_confirmed"] = self.request.GET.get("order") == "confirmed"
        return context
