from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from menu.models import Category, MenuItem, Table
from orders.models import Order, OrderItem


class AdminDashboardOrderDetailsTests(TestCase):
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

        self.client.login(username="admin1", password="pass12345")

    def test_dashboard_shows_order_details(self):
        response = self.client.get(reverse("administrator:admin-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order Details &amp; Status")
        self.assertContains(response, "alice")
        self.assertContains(response, "Table 1")
        self.assertContains(response, "Burger x 1")

    def test_dashboard_filters_by_table_and_customer(self):
        response = self.client.get(
            reverse("administrator:admin-dashboard"),
            {"table": "2", "customer": "bob"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bob")
        self.assertContains(response, "Table 2")
        self.assertNotContains(response, "alice")
