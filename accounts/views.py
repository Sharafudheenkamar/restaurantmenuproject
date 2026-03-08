from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.crypto import get_random_string
from django.views.generic import CreateView, FormView, TemplateView

from orders.models import Order

from .forms import EmailOrUsernameAuthenticationForm, ForgotPasswordEmailForm, SignupForm


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "auth/signup.html"
    success_url = reverse_lazy("login")


class CustomLoginView(LoginView):
    template_name = "auth/login.html"
    form_class = EmailOrUsernameAuthenticationForm

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


class ForgotPasswordView(FormView):
    template_name = "auth/password_reset_form.html"
    form_class = ForgotPasswordEmailForm
    success_url = reverse_lazy("accounts:password_reset_done")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = get_user_model().objects.get(email__iexact=email)

        temp_password = get_random_string(10)
        user.set_password(temp_password)
        user.save(update_fields=["password"])

        send_mail(
            subject="Your temporary password",
            message=(
                f"Hi {user.username},\n\n"
                "Your password has been reset successfully. "
                "Use the temporary password below to login and then change it from your profile.\n\n"
                f"Temporary Password: {temp_password}\n\n"
                "Login page: /login/\n"
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "auth/profile.html"

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
