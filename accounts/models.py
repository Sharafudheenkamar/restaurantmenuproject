from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('kitchen', 'Kitchen Staff'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, blank=True)
    managed_by = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='staff_members',
        null=True,
        blank=True,
    )
