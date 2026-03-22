from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cart.models import Cart, CartItem

from .models import Category, MenuItem, Table


class MenuViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="menuuser", password="pass12345")
        self.admin1 = user_model.objects.create_user(
            username="menuadmin1",
            password="pass12345",
            role="admin",
            email="menuadmin1@example.com",
        )
        self.admin2 = user_model.objects.create_user(
            username="menuadmin2",
            password="pass12345",
            role="admin",
            email="menuadmin2@example.com",
        )
        self.cat1 = Category.objects.create(owner=self.admin1, name="Starters")
        self.cat2 = Category.objects.create(owner=self.admin2, name="Desserts")
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

    def set_menu_admin(self, admin):
        session = self.client.session
        session["menu_admin_id"] = admin.id
        session.save()

    def test_menu_without_scan_or_admin_code_shows_admin_prompt(self):
        response = self.client.get(reverse("menu:menu-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrator Code")
        self.assertContains(response, "Enter the administrator code")

    def test_menu_valid_admin_code_shows_confirmation_prompt(self):
        response = self.client.post(reverse("menu:menu-list"), {"admin_code": str(self.admin1.id)})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.admin1.username)
        self.assertContains(response, "Yes, open menu")

    def test_menu_confirmed_admin_code_redirects_and_stores_admin(self):
        response = self.client.post(
            reverse("menu:menu-list"),
            {"admin_code": str(self.admin1.id), "confirm": "yes"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("menu:menu-list"))
        self.assertEqual(self.client.session.get("menu_admin_id"), self.admin1.id)
        self.assertNotIn("table", self.client.session)

    def test_menu_shows_only_selected_admin_categories(self):
        self.set_menu_admin(self.admin1)

        response = self.client.get(reverse("menu:menu-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cat1.name)
        self.assertNotContains(response, self.cat2.name)
        self.assertContains(response, self.admin1.username)
        self.assertContains(response, f"Administrator Code: {self.admin1.id}")

    def test_menu_filters_by_category(self):
        self.set_menu_admin(self.admin1)

        response = self.client.get(reverse("menu:menu-list"), {"category": self.cat1.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item1.name)
        self.assertNotContains(response, self.item2.name)

    def test_menu_has_order_history_button(self):
        self.set_menu_admin(self.admin1)
        response = self.client.get(reverse("menu:menu-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order History")
        self.assertContains(response, reverse("accounts:profile"))

    def test_menu_has_email_button(self):
        self.set_menu_admin(self.admin1)
        response = self.client.get(reverse("menu:menu-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email Us")
        self.assertContains(response, "mailto:support@restaurant.com")

    def test_menu_has_mobile_responsive_styles(self):
        self.set_menu_admin(self.admin1)
        response = self.client.get(reverse("menu:menu-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@media (max-width: 768px)")
        self.assertContains(response, "position:sticky")
        self.assertContains(response, "grid-template-columns:1fr")

    def test_menu_shows_current_cart_badge_and_total(self):
        self.client.login(username="menuuser", password="pass12345")
        self.set_menu_admin(self.admin1)
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, item=self.item1, quantity=2)

        response = self.client.get(reverse("menu:menu-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="cartCount">1<')
        self.assertContains(response, '100.00')

    def test_reset_admin_query_clears_selected_admin(self):
        self.client.login(username="menuuser", password="pass12345")
        self.set_menu_admin(self.admin1)
        Cart.objects.create(user=self.user)

        response = self.client.get(reverse("menu:menu-list"), {"reset_admin": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrator Code")
        self.assertNotIn("menu_admin_id", self.client.session)
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_table_menu_filters_items_to_table_owner(self):
        response = self.client.get(reverse("menu:table-menu", args=[self.table1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item1.name)
        self.assertNotContains(response, self.item2.name)

    def test_table_menu_scan_stores_table_id_in_session(self):
        self.client.get(reverse("menu:table-menu", args=[self.table1.id]))

        self.assertEqual(self.client.session.get("table"), self.table1.id)
        self.assertEqual(self.client.session.get("menu_admin_id"), self.admin1.id)

    def test_table_menu_only_shows_table_owner_categories(self):
        response = self.client.get(reverse("menu:table-menu", args=[self.table1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cat1.name)
        self.assertNotContains(response, self.cat2.name)
