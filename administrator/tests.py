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
        self.other_admin = user_model.objects.create_user(
            username="admin2",
            password="pass12345",
            role="admin",
            email="admin2@example.com",
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
        self.kitchen_staff = user_model.objects.create_user(
            username="kitchen_admin1",
            password="pass12345",
            role="kitchen",
            email="kitchen_admin1@example.com",
            managed_by=self.admin,
        )
        self.other_kitchen_staff = user_model.objects.create_user(
            username="kitchen_admin2",
            password="pass12345",
            role="kitchen",
            email="kitchen_admin2@example.com",
            managed_by=self.other_admin,
        )

        table1 = Table.objects.create(owner=self.admin, number=1, capacity=4)
        table2 = Table.objects.create(owner=self.admin, number=2, capacity=4)
        self.other_table = Table.objects.create(owner=self.other_admin, number=9, capacity=6)
        category = Category.objects.create(owner=self.admin, name="Main")
        item = MenuItem.objects.create(owner=self.admin, category=category, name="Burger", price="100.00", is_available=True)

        order1 = Order.objects.create(user=self.customer1, table=table1, status="pending")
        order2 = Order.objects.create(user=self.customer2, table=table2, status="served")
        OrderItem.objects.create(order=order1, menu_item=item, quantity=1)
        OrderItem.objects.create(order=order2, menu_item=item, quantity=2)

        Payment.objects.create(order=order2, amount="200.00", payment_method="CASH", is_success=True)
        other_order = Order.objects.create(user=self.customer2, table=self.other_table, status="preparing")
        OrderItem.objects.create(order=other_order, menu_item=item, quantity=3)
        Payment.objects.create(order=other_order, amount="300.00", payment_method="UPI", is_success=True)

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
        self.assertNotContains(response, "Table 9")
        self.assertNotContains(response, "bob")

    def test_orders_page_only_shows_owned_tables_without_filters(self):
        response = self.client.get(reverse("administrator:admin-orders"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Table 1")
        self.assertContains(response, "Table 2")
        self.assertNotContains(response, "Table 9")

    def test_payments_page_shows_details_and_filter(self):
        response = self.client.get(
            reverse("administrator:admin-payments"),
            {"table": "2", "customer": "bob"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Paid")
        self.assertContains(response, "Table 2")
        self.assertNotContains(response, "Table 9")
        self.assertNotContains(response, "alice")

    def test_payments_page_only_shows_owned_tables_without_filters(self):
        response = self.client.get(reverse("administrator:admin-payments"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Table 2")
        self.assertNotContains(response, "Table 9")
        self.assertNotContains(response, "300.00")

    def test_analytics_page_loads(self):
        response = self.client.get(reverse("administrator:admin-analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Analytics")
        self.assertContains(response, "Total Orders")
        self.assertEqual(response.context["total_orders"], 2)
        self.assertEqual(response.context["preparing_orders"], 0)
        self.assertEqual(response.context["total_revenue"], 200)

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
        self.assertEqual(created_user.managed_by, self.admin)

    def test_staff_list_only_shows_logged_in_admin_staff(self):
        response = self.client.get(reverse("administrator:admin-staff"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.kitchen_staff.username)
        self.assertNotContains(response, self.other_kitchen_staff.username)

    def test_edit_staff_page_has_password_field(self):
        response = self.client.get(reverse("administrator:edit-staff", args=[self.kitchen_staff.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'name="email"')
        self.assertNotContains(response, 'name="role"')

    def test_edit_staff_can_update_password(self):
        response = self.client.post(
            reverse("administrator:edit-staff", args=[self.kitchen_staff.id]),
            {
                "email": self.kitchen_staff.email,
                "password": "newpass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.kitchen_staff.refresh_from_db()
        self.assertTrue(self.kitchen_staff.check_password("newpass123"))
        self.assertEqual(self.kitchen_staff.role, "kitchen")

    def test_edit_staff_can_update_email(self):
        response = self.client.post(
            reverse("administrator:edit-staff", args=[self.kitchen_staff.id]),
            {
                "email": "updated_kitchen@example.com",
                "password": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.kitchen_staff.refresh_from_db()
        self.assertEqual(self.kitchen_staff.email, "updated_kitchen@example.com")

    def test_edit_staff_rejects_duplicate_email(self):
        response = self.client.post(
            reverse("administrator:edit-staff", args=[self.kitchen_staff.id]),
            {
                "email": "alice@example.com",
                "password": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email already exists")

    def test_cannot_edit_other_admin_staff(self):
        response = self.client.get(reverse("administrator:edit-staff", args=[self.other_kitchen_staff.id]))

        self.assertEqual(response.status_code, 404)

    def test_category_list_only_shows_logged_in_admin_categories(self):
        own_category = Category.objects.create(owner=self.admin, name="Own Category")
        Category.objects.create(owner=self.other_admin, name="Other Category")

        response = self.client.get(reverse("administrator:category-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_category.name)
        self.assertNotContains(response, "Other Category")

    def test_add_category_assigns_logged_in_admin_as_owner(self):
        response = self.client.post(reverse("administrator:category-add"), {"name": "New Category"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(owner=self.admin, name="New Category").exists())

    def test_cannot_edit_other_admin_category(self):
        foreign_category = Category.objects.create(owner=self.other_admin, name="Foreign Category")

        response = self.client.get(reverse("administrator:category-edit", args=[foreign_category.id]))

        self.assertEqual(response.status_code, 404)

    def test_generate_qr_uses_current_request_host(self):
        table = Table.objects.create(owner=self.admin, number=9, capacity=4)

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
        self.assertEqual(
            generated_url,
            "http://example.com:9000/login/?next=%2Fmenu%2Ftable%2F" + str(table.id) + "%2F",
        )

    def test_tables_page_shows_administrator_code_below_generated_qr(self):
        table = Table.objects.create(owner=self.admin, number=10, capacity=4)
        TableQR.objects.create(table=table, qr_image="qr/test.png")

        response = self.client.get(reverse("administrator:admin-tables"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Administrator Code: {self.admin.id}")


class AdminTableOwnershipTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="owner_admin",
            password="pass12345",
            role="admin",
            email="owner_admin@example.com",
        )
        self.other_admin = user_model.objects.create_user(
            username="other_admin",
            password="pass12345",
            role="admin",
            email="other_admin@example.com",
        )
        self.owned_table = Table.objects.create(owner=self.admin, number=11, capacity=4)
        self.other_table = Table.objects.create(owner=self.other_admin, number=99, capacity=8)
        self.client.login(username="owner_admin", password="pass12345")

    def test_table_list_only_shows_logged_in_admin_tables(self):
        response = self.client.get(reverse("administrator:admin-tables"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "11")
        self.assertContains(response, "4")
        self.assertNotContains(response, "99")

    def test_add_table_assigns_logged_in_admin_as_owner(self):
        response = self.client.post(
            reverse("administrator:add-table"),
            {"number": "12", "capacity": "2"},
        )

        self.assertEqual(response.status_code, 302)
        created_table = Table.objects.get(owner=self.admin, number=12)
        self.assertEqual(created_table.capacity, 2)

    def test_delete_table_cannot_remove_other_admin_table(self):
        response = self.client.post(reverse("administrator:delete-table", args=[self.other_table.id]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Table.objects.filter(id=self.other_table.id).exists())

    def test_generate_qr_cannot_access_other_admin_table(self):
        response = self.client.post(reverse("administrator:generate-qr", args=[self.other_table.id]))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(TableQR.objects.filter(table=self.other_table).exists())

    def test_menu_edit_cannot_access_other_admin_item(self):
        category = Category.objects.create(owner=self.other_admin, name="Shared")
        other_item = MenuItem.objects.create(owner=self.other_admin, category=category, name="Secret Dish", price="42.00", is_available=True)

        response = self.client.get(reverse("administrator:admin-menu-edit", args=[other_item.id]))

        self.assertEqual(response.status_code, 404)
