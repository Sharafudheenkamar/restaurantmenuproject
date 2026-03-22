from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cart.models import Cart, CartItem

from .models import Category, MenuItem


class MenuViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="menuuser", password="pass12345")
        self.cat1 = Category.objects.create(name="Starters")
        self.cat2 = Category.objects.create(name="Desserts")
        self.item1 = MenuItem.objects.create(
            category=self.cat1,
            name="Soup",
            price="50.00",
            is_available=True,
        )
        self.item2 = MenuItem.objects.create(
            category=self.cat2,
            name="Ice Cream",
            price="80.00",
            is_available=True,
        )

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
