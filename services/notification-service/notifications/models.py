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
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.CharField(max_length=255)  # Email, phone, etc.
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    related_order_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} to {self.recipient} - {self.status}"


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
