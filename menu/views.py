from cart.models import Cart
from django.views.generic import ListView
from .models import Category, MenuItem

class TodayMenuView(ListView):
    model = MenuItem
    template_name = 'user/menu.html'
    context_object_name = 'items'
    def get(self, request, *args, **kwargs):
        table = request.GET.get("table")
        if table:
            request.session["table"] = table
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = MenuItem.objects.filter(is_available=True).select_related("category")
        category_id = self.request.GET.get("category")

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all().order_by("name")
        context["selected_category"] = self.request.GET.get("category", "all")

        cart = Cart.objects.filter(user=self.request.user).first() if self.request.user.is_authenticated else None
        context["cart_count"] = cart.items.count() if cart else 0
        context["cart_total"] = cart.total() if cart else 0
        return context
