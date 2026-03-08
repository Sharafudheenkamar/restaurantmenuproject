from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from menu.models import Category, MenuItem, Table
from orders.models import Order, OrderItem
from payments.models import Payment


class ProfileDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="customer1",
            password="pass12345",
            role="customer",
        )
        self.client.login(username="customer1", password="pass12345")

        table = Table.objects.create(number=5, capacity=4)
        category = Category.objects.create(name="Main")
        menu_item = MenuItem.objects.create(
            category=category,
            name="Paneer Curry",
            price="120.00",
            is_available=True,
        )

        order = Order.objects.create(user=self.user, table=table, status="served")
        OrderItem.objects.create(order=order, menu_item=menu_item, quantity=2)
        Payment.objects.create(order=order, amount="240.00", payment_method="CASH", is_success=True)

    def test_profile_shows_order_history(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order History")
        self.assertContains(response, "Served")
        self.assertContains(response, "Paneer Curry x 2")
        self.assertContains(response, "CASH / ₹240.00")
