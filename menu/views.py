from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from cart.models import Cart

from .models import Category, MenuItem, Table


class TodayMenuView(ListView):
    model = MenuItem
    template_name = "user/menu.html"
    context_object_name = "items"

    def dispatch(self, request, *args, **kwargs):
        self.user_model = get_user_model()

        if request.method.lower() == "get" and request.GET.get("reset_admin"):
            request.session.pop("menu_admin_id", None)
            request.session.pop("table", None)
            if request.user.is_authenticated:
                Cart.objects.filter(user=request.user).delete()

        self.current_table = self.get_current_table()
        self.selected_admin = self.get_selected_admin()

        if self.current_table:
            previous_table_id = request.session.get("table")
            if (
                request.user.is_authenticated
                and previous_table_id
                and previous_table_id != self.current_table.id
            ):
                Cart.objects.filter(user=request.user).delete()
            request.session["table"] = self.current_table.id
            if self.current_table.owner_id:
                request.session["menu_admin_id"] = self.current_table.owner_id
                self.selected_admin = self.current_table.owner

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        admin_code = request.POST.get("admin_code", "").strip()
        confirm = request.POST.get("confirm")
        admin = self.lookup_admin(admin_code)

        if confirm == "yes" and admin:
            previous_admin_id = request.session.get("menu_admin_id")
            if (
                request.user.is_authenticated
                and previous_admin_id
                and previous_admin_id != admin.id
            ):
                Cart.objects.filter(user=request.user).delete()
            request.session["menu_admin_id"] = admin.id
            request.session.pop("table", None)
            return redirect("menu:menu-list")

        if confirm == "no":
            request.session.pop("menu_admin_id", None)
            request.session.pop("table", None)
            return redirect("accounts:login")

        return render(
            request,
            "user/menu_access.html",
            {
                "candidate_admin": admin,
                "entered_code": admin_code,
                "invalid_code": bool(admin_code) and admin is None,
            },
        )

    def lookup_admin(self, admin_code):
        if not admin_code.isdigit():
            return None
        return self.user_model.objects.filter(id=int(admin_code), role="admin").first()

    def get_current_table(self):
        table_id = (
            self.kwargs.get("table_id")
            or self.request.GET.get("table_id")
            or self.request.GET.get("table")
        )
        if not table_id:
            return None
        return get_object_or_404(Table.objects.select_related("owner"), id=table_id)

    def get_selected_admin(self):
        if self.current_table and self.current_table.owner_id:
            return self.current_table.owner

        admin_id = self.request.session.get("menu_admin_id")
        if not admin_id:
            return None
        return self.user_model.objects.filter(id=admin_id, role="admin").first()

    def get_template_names(self):
        if not self.selected_admin:
            return ["user/menu_access.html"]
        return [self.template_name]

    def get_queryset(self):
        queryset = MenuItem.objects.filter(is_available=True).select_related("category", "owner")
        if self.selected_admin:
            queryset = queryset.filter(owner=self.selected_admin)
        else:
            queryset = queryset.none()

        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.selected_admin:
            context.setdefault("entered_code", "")
            context.setdefault("candidate_admin", None)
            context.setdefault("invalid_code", False)
            return context

        category_queryset = Category.objects.filter(owner=self.selected_admin)
        context["categories"] = category_queryset.order_by("name")
        context["selected_category"] = self.request.GET.get("category", "all")
        context["current_table"] = self.current_table
        context["selected_admin"] = self.selected_admin

        cart = (
            Cart.objects.filter(user=self.request.user).first()
            if self.request.user.is_authenticated
            else None
        )
        context["cart_count"] = cart.items.count() if cart else 0
        context["cart_total"] = cart.total() if cart else 0
        return context
