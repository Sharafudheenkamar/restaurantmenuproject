from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from menu.models import Table
from orders.models import Order


class ProfileDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="customer1",
            password="pass12345",
            role="customer",
        )
        self.client.login(username="customer1", password="pass12345")
        table = Table.objects.create(number=5, capacity=4)
        Order.objects.create(user=self.user, table=table, status="served")

    def test_profile_shows_order_history(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order History")
        self.assertContains(response, "Served")
