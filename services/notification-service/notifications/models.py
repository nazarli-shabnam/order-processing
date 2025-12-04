"""
Notification models for Notification Service.
"""
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """Notification record."""
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    notification_id = models.UUIDField(primary_key=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.CharField(max_length=255)  # Email, phone, etc.
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    related_order_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} to {self.recipient} - {self.status}"

