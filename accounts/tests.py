from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from menu.models import Category, MenuItem, Table
from orders.models import Order, OrderItem
from payments.models import Payment


class ProfileDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="customer1",
            email="customer1@example.com",
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

    def test_profile_has_change_password_option(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, reverse("accounts:password_change"))
        self.assertContains(response, "Change Password")


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="customer2",
            email="customer2@example.com",
            password="pass12345",
            role="customer",
        )

    def test_customer_can_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "customer2@example.com", "password": "pass12345"},
        )
        self.assertEqual(response.status_code, 302)

    def test_password_reset_sends_temporary_password_email(self):
        old_password = "pass12345"
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "customer2@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Temporary Password:", mail.outbox[0].body)

        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(old_password))

    def test_customer_can_login_with_temporary_password_from_email(self):
        self.client.post(
            reverse("accounts:password_reset"),
            {"email": "customer2@example.com"},
        )
        email_body = mail.outbox[0].body
        temp_password_line = [
            line for line in email_body.splitlines() if line.startswith("Temporary Password:")
        ][0]
        temp_password = temp_password_line.split(":", 1)[1].strip()

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "customer2@example.com", "password": temp_password},
        )
        self.assertEqual(response.status_code, 302)
