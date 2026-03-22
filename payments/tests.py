from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from menu.models import Category, MenuItem, Table
from orders.models import Order, OrderItem
from payments.models import Payment


class MakePaymentViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="cust1",
            password="pass12345",
            role="customer",
            email="cust1@example.com",
        )
        self.client.login(username="cust1", password="pass12345")

        table = Table.objects.create(number=3, capacity=4)
        category = Category.objects.create(name="Main")
        item = MenuItem.objects.create(category=category, name="Pasta", price="150.00", is_available=True)

        self.order = Order.objects.create(user=self.user, table=table, status="pending")
        OrderItem.objects.create(order=self.order, menu_item=item, quantity=2)

    def test_payment_page_shows_order_details_and_unpaid_status(self):
        response = self.client.get(reverse("make-payment", args=[self.order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order Details")
        self.assertContains(response, "Pasta")
        self.assertContains(response, "Not Paid")
        self.assertContains(response, "⬅ Back to Cart")
        self.assertContains(response, "300.00")

    def test_post_payment_marks_payment_success(self):
        response = self.client.post(reverse("make-payment", args=[self.order.id]), {"method": "CASH"})
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get(order=self.order)
        self.assertTrue(payment.is_success)
        self.assertEqual(payment.payment_method, "CASH")
