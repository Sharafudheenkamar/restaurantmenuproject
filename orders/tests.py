from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from menu.models import Table
from .models import Order


class KitchenDashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.kitchen_user = User.objects.create_user(
            username="kitchen1",
            password="pass12345",
            role="kitchen",
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

        self.table1 = Table.objects.create(number=1, capacity=4)
        self.table2 = Table.objects.create(number=2, capacity=4)

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
            {"customer": self.customer2.id, "table": self.table2.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cust2")
        self.assertNotContains(response, "cust1")
        self.assertContains(response, "Table 2")
