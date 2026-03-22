from django.conf import settings
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
import uuid

class Table(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tables",
        null=True,
        blank=True,
    )
    number = models.PositiveIntegerField()
    capacity = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "number"], name="unique_table_number_per_owner"),
        ]
        ordering = ["number"]

    def __str__(self):
        return f"Table {self.number}"


class TableQR(models.Model):
    table = models.OneToOneField(Table, on_delete=models.CASCADE,related_name='qr_map')
    qr_image = models.ImageField(upload_to="qr/", blank=True, null=True)
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"QR for Table {self.table.number}"


