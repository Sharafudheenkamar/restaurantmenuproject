from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView

from menu.models import MenuItem

from .models import Cart, CartItem


class AddToCartView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "login required"}, status=403)

        item = get_object_or_404(MenuItem, id=request.POST.get("item_id"))
        qty = int(request.POST.get("qty", 1))

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            item=item,
            defaults={"quantity": 0},
        )

        if created:
            cart_item.quantity = qty
        else:
            cart_item.quantity += qty

        cart_item.save()

        return JsonResponse(
            {
                "status": "added",
                "cart_count": cart.items.count(),
                "total": float(cart.total()),
            }
        )


class CartPageView(LoginRequiredMixin, TemplateView):
    template_name = "cart/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        context["cart"] = cart
        context["items"] = cart.items.select_related("item")

        return context


class RemoveCartItemView(View):
    def post(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "login required"}, status=403)

        cart = Cart.objects.filter(user=request.user).first()
        CartItem.objects.filter(id=pk, cart__user=request.user).delete()

        if not cart:
            return JsonResponse({"success": True, "count": 0, "total": 0})

        return JsonResponse(
            {
                "success": True,
                "count": cart.items.count(),
                "total": float(cart.total()),
            }
        )


class ClearCartView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "login required"}, status=403)

        Cart.objects.filter(user=request.user).delete()
        return JsonResponse({"status": "cleared", "count": 0, "total": 0})
