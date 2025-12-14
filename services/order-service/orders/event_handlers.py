"""
Event handlers for Order Service.
These functions process events from the message queue.
"""
from .models import Order, OrderItem, ProcessedEvent
from events.publisher import RedisStreamPublisher
from events.schemas import OrderCreatedEvent, OrderStatusUpdatedEvent, EventType
import sys
from pathlib import Path
import redis
import logging
from django.conf import settings
from django.utils import timezone
from datetime import datetime

# Add shared events to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=False  # Keep bytes for Redis Streams
)

# Initialize event publisher
event_publisher = RedisStreamPublisher(redis_client)


def is_event_processed(event_id: str) -> bool:
    """Check if an event has already been processed."""
    return ProcessedEvent.objects.filter(event_id=event_id).exists()


def mark_event_processed(event_id: str, event_type: str) -> None:
    """Mark an event as processed."""
    ProcessedEvent.objects.get_or_create(
        event_id=event_id,
        defaults={'event_type': event_type}
    )


def handle_order_created(event_data: dict) -> bool:
    """
    Handle OrderCreated event.

    Creates an order in the database and updates its status to 'processing'.
    Then publishes an OrderStatusUpdated event.

    Returns:
        True if successful, False otherwise
    """
    try:
        event = OrderCreatedEvent.from_dict(event_data)

        # Check for duplicate processing
        if is_event_processed(event.event_id):
            logger.warning(
                f"Event {event.event_id} already processed, skipping")
            return True  # Already processed, so return success

        logger.info(
            f"Processing OrderCreated event for order {event.order_id}")

        # Create order
        order = Order.objects.create(
            order_id=event.order_id,
            user_id=event.user_id,
            status='pending',  # Start as pending
            total_amount=event.total_amount,
            shipping_address=event.shipping_address,
            user_email=event.user_email,
        )

        # Create order items
        for product in event.products:
            OrderItem.objects.create(
                order=order,
                product_id=product.product_id,
                quantity=product.quantity,
                price=product.price,
                name=product.name or '',
            )

        # Update status to processing
        previous_status = order.status
        order.status = 'processing'
        order.save()

        # Publish OrderStatusUpdated event
        status_event = OrderStatusUpdatedEvent(
            order_id=str(order.order_id),
            status=order.status,
            previous_status=previous_status,
            updated_at=order.updated_at.isoformat(),
            user_email=order.user_email,
        )

        success = event_publisher.publish(
            settings.EVENT_STREAM_NAME,
            status_event.to_dict()
        )

        if not success:
            logger.error(
                f"Failed to publish OrderStatusUpdated event for order {order.order_id}")
            # Order is still created, so return True
            # In production, you might want to retry or use a dead letter queue

        # Mark event as processed
        mark_event_processed(event.event_id, EventType.ORDER_CREATED.value)

        logger.info(f"Successfully processed order {order.order_id}")
        return True

    except Exception as e:
        logger.error(f"Error handling OrderCreated event: {e}", exc_info=True)
        return False


def handle_order_status_updated(event_data: dict) -> bool:
    """
    Handle OrderStatusUpdated event.

    This handler can be used if Order Service needs to react to
    status updates from other services (e.g., Payment Service).

    Currently, this service publishes these events, so this is
    mainly for future use or if other services update order status.
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

        # Update order status
        order = Order.objects.get(order_id=event.order_id)
        order.status = event.status
        order.save()

        # Mark event as processed
        mark_event_processed(
            event.event_id, EventType.ORDER_STATUS_UPDATED.value)

        logger.info(f"Updated order {order.order_id} status to {event.status}")
        return True

    except Order.DoesNotExist:
        logger.warning(f"Order {event.order_id} not found for status update")
        return False
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

    if event_type == EventType.ORDER_CREATED.value:
        return handle_order_created(event)
    elif event_type == EventType.ORDER_STATUS_UPDATED.value:
        # Order Service publishes these, but might receive them from other services
        return handle_order_status_updated(event)
    else:
        logger.warning(f"Unknown event type: {event_type}")
        return False
