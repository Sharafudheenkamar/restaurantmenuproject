import uuid
from django.db import models

class Table(models.Model):
    table_number = models.PositiveIntegerField(unique=True)
    qr_code = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return f"Table {self.table_number}"
from django.conf import settings
from django.db import models
from menu.models import MenuItem
from .models import Table

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    instructions = models.TextField(blank=True)
