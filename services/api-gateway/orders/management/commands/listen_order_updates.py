"""
Django management command to listen to order status updates from Redis Stream
and forward them to WebSocket clients via Django Channels.

This should be run as a background process alongside the Django server.

Usage:
    python manage.py listen_order_updates
"""
from events.schemas import OrderStatusUpdatedEvent, EventType
import sys
import json
from pathlib import Path
import redis
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Add shared events to path
sys.path.insert(0, str(Path(__file__).resolve().parents[6] / 'shared'))

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Listen to order status updates from Redis Stream and forward to WebSocket clients'

    def handle(self, *args, **options):
        """Start listening to order status updates."""
        self.stdout.write(self.style.SUCCESS(
            'Starting order status update listener...'))

        # Initialize Redis client
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=False  # Keep bytes for Redis Streams
        )

        # Get channel layer
        channel_layer = get_channel_layer()

        # Consumer group for this listener
        consumer_group = 'websocket-listeners'
        consumer_name = 'websocket-listener-1'
        stream_name = settings.EVENT_STREAM_NAME

        # Create consumer group if it doesn't exist
        try:
            redis_client.xgroup_create(
                stream_name, consumer_group, id="0", mkstream=True
            )
        except Exception:
            # Group already exists, that's fine
            pass

        self.stdout.write(
            self.style.SUCCESS(
                f'Listening to stream: {stream_name}\n'
                f'Consumer group: {consumer_group}\n'
                f'Consumer name: {consumer_name}'
            )
        )

        try:
            while True:
                # Read from stream
                messages = redis_client.xreadgroup(
                    consumer_group,
                    consumer_name,
                    {stream_name: ">"},
                    count=10,
                    block=1000,  # Block for 1 second
                )

                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        try:
                            # Parse event
                            event_json = fields[b"event"].decode("utf-8")
                            event_data = json.loads(event_json)

                            # Only process OrderStatusUpdated events
                            if event_data.get('event_type') == EventType.ORDER_STATUS_UPDATED.value:
                                event = OrderStatusUpdatedEvent.from_dict(
                                    event_data)

                                # Send to channel layer for the specific order
                                room_group_name = f'order_{event.order_id}'

                                async_to_sync(channel_layer.group_send)(
                                    room_group_name,
                                    {
                                        'type': 'order_status_update',
                                        'order_id': event.order_id,
                                        'status': event.status,
                                        'previous_status': event.previous_status,
                                        'updated_at': event.updated_at,
                                    }
                                )

                                # Acknowledge message
                                redis_client.xack(
                                    stream_name, consumer_group, msg_id)

                                logger.info(
                                    f"Forwarded order status update for order {event.order_id} "
                                    f"to WebSocket clients"
                                )
                            else:
                                # Acknowledge other events but don't process
                                redis_client.xack(
                                    stream_name, consumer_group, msg_id)

                        except Exception as e:
                            logger.error(
                                f"Error processing message {msg_id}: {e}",
                                exc_info=True,
                            )
                            # Don't acknowledge on error - will be retried

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nStopping listener...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            raise
