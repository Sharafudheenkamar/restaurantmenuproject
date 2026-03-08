from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from menu.models import Category, MenuItem

from .models import Cart


class CartFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="customer1",
            password="pass12345",
        )
        self.client.login(username="customer1", password="pass12345")
        self.category = Category.objects.create(name="Main Course")
        self.item = MenuItem.objects.create(
            category=self.category,
            name="Paneer Curry",
            price="100.00",
            is_available=True,
        )

    def test_add_to_cart_uses_quantity_for_new_item(self):
        response = self.client.post(reverse("cart-add"), {"item_id": self.item.id, "qty": 2})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["cart_count"], 1)

        cart = Cart.objects.get(user=self.user)
        cart_item = cart.items.get(item=self.item)
        self.assertEqual(cart_item.quantity, 2)

    def test_remove_item_returns_updated_count(self):
        self.client.post(reverse("cart-add"), {"item_id": self.item.id, "qty": 1})
        cart = Cart.objects.get(user=self.user)
        cart_item = cart.items.get(item=self.item)

        response = self.client.post(reverse("cart-remove", args=[cart_item.id]))
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["count"], 0)
