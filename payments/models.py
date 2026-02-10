from django.db import models
from orders.models import Order
class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    is_success = models.BooleanField(default=False)
    paid_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"Payment #{self.id} - {self.order.id}"

