from django.http import JsonResponse
from django.views import View
from menu.models import MenuItem
from .utils import Cart

class AddToCartView(View):
    def post(self, request):
        cart = Cart(request)
        item = MenuItem.objects.get(id=request.POST.get('item_id'))
        qty = int(request.POST.get('qty', 1))

        cart.add(item.id, item.price, qty)
        return JsonResponse({'status': 'added'})
