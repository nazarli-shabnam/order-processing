from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_id', 'notification_type', 'recipient', 'status', 'created_at', 'sent_at']
    list_filter = ['notification_type', 'status', 'created_at']
    search_fields = ['recipient', 'related_order_id']
    readonly_fields = ['notification_id', 'created_at', 'sent_at']

