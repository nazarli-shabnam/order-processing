"""
WebSocket consumers for real-time order status updates.
"""
import json
import sys
from pathlib import Path
import redis
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings

# Add shared events to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from events.schemas import OrderStatusUpdatedEvent

logger = logging.getLogger(__name__)

# Redis client for subscribing to events
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)


class OrderStatusConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for order status updates."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.room_group_name = f'order_{self.order_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected for order {self.order_id}")
        
        # Start listening to Redis Stream for this order
        await self.listen_to_order_updates()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for order {self.order_id}")
    
    async def listen_to_order_updates(self):
        """Listen to Redis Stream for order status updates."""
        # This is a simplified version
        # In production, you'd want a background task that listens
        # and sends updates via channel_layer
        pass
    
    async def order_status_update(self, event):
        """Receive order status update from channel layer."""
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'order_status_update',
            'order_id': event['order_id'],
            'status': event['status'],
            'previous_status': event['previous_status'],
            'updated_at': event['updated_at'],
        }))

