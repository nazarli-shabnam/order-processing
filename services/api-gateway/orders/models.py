"""
Order models for API Gateway.
This is a lightweight model just for tracking orders created through this service.
The full order data is managed by the Order Service.
"""
from django.db import models
from django.utils import timezone


class Order(models.Model):
    """Lightweight order model for API Gateway."""
    order_id = models.UUIDField(primary_key=True)
    user_id = models.UUIDField()
    status = models.CharField(max_length=50, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id} - {self.status}"

