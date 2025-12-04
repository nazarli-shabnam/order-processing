"""
Event publisher abstraction - allows switching between Redis Streams and Kafka.
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class EventPublisher(ABC):
    """Abstract base class for event publishers."""

    @abstractmethod
    def publish(self, stream_name: str, event: Dict[str, Any]) -> bool:
        """
        Publish an event to a stream.
        
        Args:
            stream_name: Name of the stream/channel
            event: Event dictionary
            
        Returns:
            True if successful, False otherwise
        """
        pass


class RedisStreamPublisher(EventPublisher):
    """Redis Streams implementation of event publisher."""
    
    def __init__(self, redis_client):
        """
        Initialize Redis Stream publisher.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client

    def publish(self, stream_name: str, event: Dict[str, Any]) -> bool:
        """Publish event to Redis Stream."""
        try:
            # Redis Streams uses XADD command
            event_id = self.redis.xadd(
                stream_name,
                {"event": json.dumps(event)},
                maxlen=10000,  # Keep last 10000 events
            )
            logger.info(
                f"Published event {event['event_id']} to stream {stream_name} "
                f"with Redis ID {event_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish event to Redis Stream: {e}")
            return False


class KafkaPublisher(EventPublisher):
    """Kafka implementation of event publisher (for future use)."""
    
    def __init__(self, kafka_producer):
        """
        Initialize Kafka publisher.
        
        Args:
            kafka_producer: Kafka producer instance
        """
        self.producer = kafka_producer

    def publish(self, stream_name: str, event: Dict[str, Any]) -> bool:
        """Publish event to Kafka topic."""
        try:
            future = self.producer.send(stream_name, value=event)
            future.get(timeout=10)  # Wait for confirmation
            logger.info(
                f"Published event {event['event_id']} to Kafka topic {stream_name}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish event to Kafka: {e}")
            return False

