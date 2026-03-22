from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from menu.models import Category, MenuItem, Table, TableQR
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

    def test_add_staff_page_only_allows_kitchen_role_ui(self):
        response = self.client.get(reverse("administrator:add-staff"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Kitchen"')
        self.assertNotContains(response, 'name="role"')

    def test_add_staff_rejects_duplicate_username(self):
        response = self.client.post(
            reverse("administrator:add-staff"),
            {
                "username": "alice",
                "email": "newkitchen@example.com",
                "password": "pass12345",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username already exists")

    def test_add_staff_rejects_duplicate_email(self):
        response = self.client.post(
            reverse("administrator:add-staff"),
            {
                "username": "newkitchen",
                "email": "alice@example.com",
                "password": "pass12345",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email already exists")

    def test_add_staff_creates_kitchen_user(self):
        response = self.client.post(
            reverse("administrator:add-staff"),
            {
                "username": "kitchen_new",
                "email": "kitchen_new@example.com",
                "password": "pass12345",
            },
        )
        self.assertEqual(response.status_code, 302)
        created_user = get_user_model().objects.get(username="kitchen_new")
        self.assertEqual(created_user.role, "kitchen")

    def test_edit_staff_page_has_password_field(self):
        response = self.client.get(reverse("administrator:edit-staff", args=[self.customer1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="password"')
        self.assertNotContains(response, 'name="role"')

    def test_edit_staff_can_update_password(self):
        response = self.client.post(
            reverse("administrator:edit-staff", args=[self.customer1.id]),
            {
                "password": "newpass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.customer1.refresh_from_db()
        self.assertTrue(self.customer1.check_password("newpass123"))
        self.assertEqual(self.customer1.role, "customer")

    def test_generate_qr_uses_current_request_host(self):
        table = Table.objects.create(number=9, capacity=4)

        class DummyQR:
            def save(self, buffer, format="PNG"):
                buffer.write(b"fake-png")

        with patch("administrator.views.qrcode.make", return_value=DummyQR()) as mock_make:
            response = self.client.post(
                reverse("administrator:generate-qr", args=[table.id]),
                HTTP_HOST="example.com:9000",
            )

        self.assertEqual(response.status_code, 302)
        qr_obj = TableQR.objects.get(table=table)
        self.assertTrue(bool(qr_obj.qr_image))
        generated_url = mock_make.call_args[0][0]
        self.assertIn("http://example.com:9000/login/", generated_url)
        self.assertIn("next=%2Fmenu%2F%3Ftable%3D9", generated_url)
