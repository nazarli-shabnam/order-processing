"""
Event handlers for Notification Service.
These functions process events and send notifications.
"""
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
from events.schemas import OrderStatusUpdatedEvent, EventType
from .models import Notification

logger = logging.getLogger(__name__)


def get_user_email_from_order(order_id: str) -> str:
    """
    Get user email from order.
    
    In a real system, you might query the Order Service API or
    have the email in the event. For now, we'll need to get it
    from the OrderCreated event or store it.
    
    This is a placeholder - you'll need to implement this based on
    your architecture (e.g., query Order Service, include in event, etc.)
    """
    # TODO: Implement this - could query Order Service or include email in event
    return "user@example.com"


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
        
        logger.info(f"Sent email notification for order {order_id} to {user_email}")
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
        
        if success:
            logger.info(f"Notification sent for order {event.order_id}")
        else:
            logger.error(f"Failed to send notification for order {event.order_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error handling OrderStatusUpdated event: {e}", exc_info=True)
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

