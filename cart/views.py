from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from menu.models import MenuItem


class AddToCartView(View):
    def post(self, request):

        if not request.user.is_authenticated:
            return JsonResponse({"error":"login required"}, status=403)

        item = get_object_or_404(MenuItem, id=request.POST.get("item_id"))
        qty = int(request.POST.get("qty", 1))

        cart, created = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            item=item
        )

        cart_item.quantity += qty
        cart_item.save()

        return JsonResponse({
            "status":"added",
            "cart_count": cart.items.count(),
            "total": cart.total()
        })


from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Cart

class CartPageView(LoginRequiredMixin, TemplateView):
    template_name = "cart/cart.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        ctx["cart"] = cart
        ctx["items"] = cart.items.all()

        return ctx
class RemoveCartItemView(View):
    def post(self, request, pk):
        CartItem.objects.filter(id=pk, cart__user=request.user).delete()
        return JsonResponse({"status":"removed"})
    


class ClearCartView(View):
    def post(self, request):
        Cart.objects.filter(user=request.user).delete()
        return JsonResponse({"status":"cleared"})