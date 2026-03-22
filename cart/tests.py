from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from menu.models import Category, MenuItem, Table
from orders.models import Order
from payments.models import Payment

from .models import Cart


class CartFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="customer1",
            password="pass12345",
        )
        self.admin = user_model.objects.create_user(
            username="cartadmin",
            password="pass12345",
            role="admin",
            email="cartadmin@example.com",
        )
        self.client.login(username="customer1", password="pass12345")
        self.category = Category.objects.create(owner=self.admin, name="Main Course")
        self.item = MenuItem.objects.create(
            owner=self.admin,
            category=self.category,
            name="Paneer Curry",
            price="100.00",
            is_available=True,
        )
        self.table = Table.objects.create(owner=self.admin, number=1, capacity=4)

    def set_menu_admin(self):
        session = self.client.session
        session["menu_admin_id"] = self.admin.id
        session.save()

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

    def test_cart_page_has_back_to_menu_button(self):
        response = self.client.get(reverse("cart-page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Back to Menu")
        self.assertContains(response, reverse("menu:menu-list"))

    def test_menu_badge_and_total_reset_after_cart_item_deleted(self):
        self.set_menu_admin()
        self.client.post(reverse("cart-add"), {"item_id": self.item.id, "qty": 1})
        cart = Cart.objects.get(user=self.user)
        cart_item = cart.items.get(item=self.item)

        self.client.post(reverse("cart-remove", args=[cart_item.id]))
        response = self.client.get(reverse("menu:menu-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="cartCount">0<')
        self.assertContains(response, '0.00')

    def test_dummy_checkout_creates_order_and_payment(self):
        session = self.client.session
        session["table"] = self.table.id
        session["menu_admin_id"] = self.admin.id
        session.save()

        self.client.post(reverse("cart-add"), {"item_id": self.item.id, "qty": 2})
        response = self.client.post(reverse("cart-checkout"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:profile"), response.url)

        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.table, self.table)
        self.assertEqual(order.items.first().quantity, 2)
        self.assertTrue(Payment.objects.filter(order=order, is_success=True).exists())
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_dummy_checkout_uses_selected_admin_table_when_not_scanned(self):
        self.set_menu_admin()
        self.client.post(reverse("cart-add"), {"item_id": self.item.id, "qty": 1})

        response = self.client.post(reverse("cart-checkout"))

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.table, self.table)
