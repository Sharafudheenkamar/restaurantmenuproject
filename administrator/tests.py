from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from menu.models import Category, MenuItem, Table
from orders.models import Order, OrderItem
from payments.models import Payment


class AdminDashboardNavigationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="admin1",
            password="pass12345",
            role="admin",
            email="admin@example.com",
        )
        self.customer1 = user_model.objects.create_user(
            username="alice",
            password="pass12345",
            role="customer",
            email="alice@example.com",
        )
        self.customer2 = user_model.objects.create_user(
            username="bob",
            password="pass12345",
            role="customer",
            email="bob@example.com",
        )

        table1 = Table.objects.create(number=1, capacity=4)
        table2 = Table.objects.create(number=2, capacity=4)
        category = Category.objects.create(name="Main")
        item = MenuItem.objects.create(category=category, name="Burger", price="100.00", is_available=True)

        order1 = Order.objects.create(user=self.customer1, table=table1, status="pending")
        order2 = Order.objects.create(user=self.customer2, table=table2, status="served")
        OrderItem.objects.create(order=order1, menu_item=item, quantity=1)
        OrderItem.objects.create(order=order2, menu_item=item, quantity=2)

        Payment.objects.create(order=order2, amount="200.00", payment_method="CASH", is_success=True)

        self.client.login(username="admin1", password="pass12345")

    def test_dashboard_contains_navigation_cards_only(self):
        response = self.client.get(reverse("administrator:admin-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("administrator:admin-orders"))
        self.assertContains(response, reverse("administrator:admin-payments"))
        self.assertNotContains(response, "Order Details &amp; Status")

    def test_orders_page_shows_order_details_and_filter(self):
        response = self.client.get(
            reverse("administrator:admin-orders"),
            {"table": "1", "customer": "alice"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Burger x 1")
        self.assertContains(response, "Table 1")
        self.assertNotContains(response, "bob")

    def test_payments_page_shows_details_and_filter(self):
        response = self.client.get(
            reverse("administrator:admin-payments"),
            {"table": "2", "customer": "bob"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paid")
        self.assertContains(response, "Table 2")
        self.assertNotContains(response, "alice")

    def test_analytics_page_loads(self):
        response = self.client.get(reverse("administrator:admin-analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Analytics")
        self.assertContains(response, "Total Orders")
