"""
Event handlers for Notification Service.
These functions process events and send notifications.
"""
from .models import Notification, ProcessedEvent
from events.schemas import OrderStatusUpdatedEvent, EventType
import sys
from pathlib import Path
import redis
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from uuid import uuid4

# Add shared events to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))

logger = logging.getLogger(__name__)


def is_event_processed(event_id: str) -> bool:
    """Check if an event has already been processed."""
    return ProcessedEvent.objects.filter(event_id=event_id).exists()


def mark_event_processed(event_id: str, event_type: str) -> None:
    """Mark an event as processed."""
    ProcessedEvent.objects.get_or_create(
        event_id=event_id,
        defaults={'event_type': event_type}
    )


def send_order_status_email(order_id: str, status: str, user_email: str) -> bool:
    """
    Send email notification about order status update.

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        status_messages = {
            'pending': 'Your order has been received and is pending.',
            'processing': 'Your order is now being processed.',
            'completed': 'Your order has been completed!',
            'cancelled': 'Your order has been cancelled.',
        }

        subject = f"Order {order_id[:8]} Status Update"
        message = f"""
Hello,

{status_messages.get(status, f'Your order status has been updated to: {status}')}

Order ID: {order_id}
Status: {status}

Thank you for your business!
        """.strip()

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )

        logger.info(
            f"Sent email notification for order {order_id} to {user_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email notification: {e}", exc_info=True)
        return False


def handle_order_status_updated(event_data: dict) -> bool:
    """
    Handle OrderStatusUpdated event.

    Sends email notification to the user about the status change.

    Returns:
        True if handled successfully, False otherwise
    """
    try:
        event = OrderStatusUpdatedEvent.from_dict(event_data)

        # Check for duplicate processing
        if is_event_processed(event.event_id):
            logger.warning(
                f"Event {event.event_id} already processed, skipping")
            return True  # Already processed, so return success

        logger.info(
            f"Processing OrderStatusUpdated event for order {event.order_id}: "
            f"{event.previous_status} -> {event.status}"
        )

        # Get user email from event
        user_email = event.user_email

        # Send email notification
        success = send_order_status_email(
            order_id=event.order_id,
            status=event.status,
            user_email=user_email,
        )

        # Record notification
        notification = Notification.objects.create(
            notification_id=uuid4(),
            notification_type='email',
            recipient=user_email,
            subject=f"Order {event.order_id[:8]} Status Update",
            message=f"Order status updated to {event.status}",
            status='sent' if success else 'failed',
            related_order_id=event.order_id,
            sent_at=timezone.now() if success else None,
        )

        # Mark event as processed
        mark_event_processed(
            event.event_id, EventType.ORDER_STATUS_UPDATED.value)

        if success:
            logger.info(f"Notification sent for order {event.order_id}")
        else:
            logger.error(
                f"Failed to send notification for order {event.order_id}")

        return success

    except Exception as e:
        logger.error(
            f"Error handling OrderStatusUpdated event: {e}", exc_info=True)
        return False


def route_event(event: dict) -> bool:
    """
    Route events to appropriate handlers.

    Args:
        event: Event dictionary

    Returns:
        True if handled successfully, False otherwise
    """
    event_type = event.get('event_type')

    if event_type == EventType.ORDER_STATUS_UPDATED.value:
        return handle_order_status_updated(event)
    else:
        # Notification service only handles status updates for now
        logger.debug(f"Ignoring event type: {event_type}")
        return True  # Not an error, just not handled
