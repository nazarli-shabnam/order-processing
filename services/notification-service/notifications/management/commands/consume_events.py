"""
Django management command to consume events from the message queue.
Run this command to start the Notification Service event consumer.

Usage:
    python manage.py consume_events
"""
import sys
from pathlib import Path
import redis
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

# Add shared events to path
sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'shared'))
from events.consumer import RedisStreamConsumer
from notifications.event_handlers import route_event

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Consume events from the message queue'

    def handle(self, *args, **options):
        """Start consuming events."""
        self.stdout.write(self.style.SUCCESS('Starting Notification Service event consumer...'))
        
        # Initialize Redis client
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=False  # Keep bytes for Redis Streams
        )
        
        # Initialize consumer
        consumer = RedisStreamConsumer(redis_client)
        
        # Start consuming
        self.stdout.write(
            self.style.SUCCESS(
                f'Consuming from stream: {settings.EVENT_STREAM_NAME}\n'
                f'Consumer group: {settings.CONSUMER_GROUP}\n'
                f'Consumer name: {settings.CONSUMER_NAME}'
            )
        )
        
        try:
            consumer.consume(
                stream_name=settings.EVENT_STREAM_NAME,
                consumer_group=settings.CONSUMER_GROUP,
                consumer_name=settings.CONSUMER_NAME,
                handler=route_event,
                block=1000,  # Block for 1 second
            )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nStopping consumer...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            raise

