from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from menu.models import Table
from .models import Order


class KitchenDashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username="admin1", password="pass12345", role="admin")
        self.other_admin = User.objects.create_user(username="admin2", password="pass12345", role="admin")
        self.kitchen_user = User.objects.create_user(
            username="kitchen1",
            password="pass12345",
            role="kitchen",
            managed_by=self.admin,
        )
        self.other_kitchen_user = User.objects.create_user(
            username="kitchen2",
            password="pass12345",
            role="kitchen",
            managed_by=self.other_admin,
        )
        self.customer1 = User.objects.create_user(
            username="cust1",
            password="pass12345",
            role="customer",
        )
        self.customer2 = User.objects.create_user(
            username="cust2",
            password="pass12345",
            role="customer",
        )

        self.table1 = Table.objects.create(owner=self.admin, number=1, capacity=4)
        self.table2 = Table.objects.create(owner=self.other_admin, number=2, capacity=4)

        Order.objects.create(user=self.customer1, table=self.table1, status="pending")
        Order.objects.create(user=self.customer2, table=self.table2, status="served")

        self.client.login(username="kitchen1", password="pass12345")

    def test_kitchen_dashboard_shows_logout_and_history_section(self):
        response = self.client.get(reverse("kitchen-orders"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Logout")
        self.assertContains(response, "Order History")

    def test_kitchen_dashboard_filters_by_customer_and_table(self):
        response = self.client.get(
            reverse("kitchen-orders"),
            {"customer": self.customer1.id, "table": self.table1.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cust1")
        self.assertNotContains(response, "cust2")
        self.assertContains(response, "Table 1")
        self.assertNotContains(response, "Table 2")

    def test_kitchen_dashboard_only_shows_orders_for_managing_admin_tables(self):
        response = self.client.get(reverse("kitchen-orders"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cust1")
        self.assertNotContains(response, "cust2")
        self.assertNotContains(response, "Table 2")


    def test_kitchen_cannot_update_order_for_other_admin_table(self):
        foreign_order = Order.objects.get(table=self.table2)

        response = self.client.get(reverse("update-order", args=[foreign_order.id]))

        self.assertEqual(response.status_code, 404)
