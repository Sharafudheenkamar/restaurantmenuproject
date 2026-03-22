from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cart.models import Cart, CartItem

from .models import Category, MenuItem, Table


class MenuViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="menuuser", password="pass12345")
        self.admin1 = user_model.objects.create_user(username="menuadmin1", password="pass12345", role="admin")
        self.admin2 = user_model.objects.create_user(username="menuadmin2", password="pass12345", role="admin")
        self.cat1 = Category.objects.create(name="Starters")
        self.cat2 = Category.objects.create(name="Desserts")
        self.item1 = MenuItem.objects.create(
            owner=self.admin1,
            category=self.cat1,
            name="Soup",
            price="50.00",
            is_available=True,
        )
        self.item2 = MenuItem.objects.create(
            owner=self.admin2,
            category=self.cat2,
            name="Ice Cream",
            price="80.00",
            is_available=True,
        )
        self.table1 = Table.objects.create(owner=self.admin1, number=1, capacity=4)
        self.table2 = Table.objects.create(owner=self.admin2, number=2, capacity=4)

    def test_menu_shows_categories(self):
        response = self.client.get(reverse("menu:menu-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cat1.name)
        self.assertContains(response, self.cat2.name)

    def test_menu_filters_by_category(self):
        response = self.client.get(reverse("menu:menu-list"), {"category": self.cat1.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item1.name)
        self.assertNotContains(response, self.item2.name)

    def test_menu_has_order_history_button(self):
        response = self.client.get(reverse("menu:menu-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order History")
        self.assertContains(response, reverse("accounts:profile"))


    def test_menu_has_email_button(self):
        response = self.client.get(reverse("menu:menu-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email Us")
        self.assertContains(response, "mailto:support@restaurant.com")

    def test_menu_shows_current_cart_badge_and_total(self):
        self.client.login(username="menuuser", password="pass12345")
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, item=self.item1, quantity=2)

        response = self.client.get(reverse("menu:menu-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="cartCount">1<')
        self.assertContains(response, '100.00')


    def test_table_menu_filters_items_to_table_owner(self):
        response = self.client.get(reverse("menu:table-menu", args=[self.table1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item1.name)
        self.assertNotContains(response, self.item2.name)

    def test_table_menu_scan_stores_table_id_in_session(self):
        self.client.get(reverse("menu:table-menu", args=[self.table1.id]))

        self.assertEqual(self.client.session.get("table"), self.table1.id)
