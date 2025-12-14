"""
Order models for Order Service.
This is the source of truth for order data.
"""
from django.db import models
from django.utils import timezone
import uuid


class Order(models.Model):
    """Order model - source of truth for orders."""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = models.UUIDField()
    status = models.CharField(
        max_length=50, choices=ORDER_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    user_email = models.EmailField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id} - {self.status}"


class OrderItem(models.Model):
    """Order item model."""
    order = models.ForeignKey(
        Order, related_name='items', on_delete=models.CASCADE)
    product_id = models.UUIDField()
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f"{self.quantity}x {self.product_id} for Order {self.order.order_id}"


class ProcessedEvent(models.Model):
    """Track processed events to prevent duplicate processing."""
    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'processed_events'
        ordering = ['-processed_at']
        indexes = [
            models.Index(fields=['event_id']),
            models.Index(fields=['event_type', 'processed_at']),
        ]

    def __str__(self):
        return f"Event {self.event_id} ({self.event_type}) processed at {self.processed_at}"
