from cart.models import Cart
from django.views.generic import ListView
from django.shortcuts import get_object_or_404

from .models import Category, MenuItem, Table

class TodayMenuView(ListView):
    model = MenuItem
    template_name = 'user/menu.html'
    context_object_name = 'items'

    def dispatch(self, request, *args, **kwargs):
        self.current_table = self.get_current_table()
        if self.current_table:
            request.session["table"] = self.current_table.id
        return super().dispatch(request, *args, **kwargs)

    def get_current_table(self):
        table_id = self.kwargs.get("table_id") or self.request.GET.get("table_id") or self.request.GET.get("table")
        if not table_id:
            return None
        return get_object_or_404(Table.objects.select_related("owner"), id=table_id)

    def get_queryset(self):
        queryset = MenuItem.objects.filter(is_available=True).select_related("category", "owner")
        if self.current_table and self.current_table.owner_id:
            queryset = queryset.filter(owner=self.current_table.owner)

        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_queryset = Category.objects.all()
        if self.current_table and self.current_table.owner_id:
            category_queryset = category_queryset.filter(menuitem__owner=self.current_table.owner).distinct()
        context["categories"] = category_queryset.order_by("name")
        context["selected_category"] = self.request.GET.get("category", "all")
        context["current_table"] = self.current_table

        cart = Cart.objects.filter(user=self.request.user).first() if self.request.user.is_authenticated else None
        context["cart_count"] = cart.items.count() if cart else 0
        context["cart_total"] = cart.total() if cart else 0
        return context
