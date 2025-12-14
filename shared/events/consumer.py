"""
Event consumer abstraction - allows switching between Redis Streams and Kafka.
"""
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventConsumer(ABC):
    """Abstract base class for event consumers."""

    @abstractmethod
    def consume(
        self,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        handler: Callable[[Dict[str, Any]], bool],
        block: int = 1000,
    ):
        """
        Consume events from a stream.

        Args:
            stream_name: Name of the stream/channel
            consumer_group: Consumer group name
            consumer_name: Unique consumer name
            handler: Function to process events (returns True if successful)
            block: Block time in milliseconds
        """
        pass


class RedisStreamConsumer(EventConsumer):
    """Redis Streams implementation of event consumer."""

    def __init__(self, redis_client):
        """
        Initialize Redis Stream consumer.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client

    def _process_with_retry(
        self, handler: Callable, event: Dict[str, Any], max_retries: int = 3
    ) -> bool:
        """
        Process event with exponential backoff retry logic.

        Args:
            handler: Event handler function
            event: Event dictionary
            max_retries: Maximum number of retry attempts

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                success = handler(event)
                if success:
                    return True
                else:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(
                            f"Handler returned False for event {event.get('event_id')}. "
                            f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"Handler failed after {max_retries} attempts for event "
                            f"{event.get('event_id')}"
                        )
                        return False
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Error processing event {event.get('event_id')}: {e}. "
                        f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Error processing event {event.get('event_id')} after "
                        f"{max_retries} attempts: {e}",
                        exc_info=True,
                    )
                    return False
        return False

    def consume(
        self,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        handler: Callable[[Dict[str, Any]], bool],
        block: int = 1000,
    ):
        """Consume events from Redis Stream."""
        try:
            # Create consumer group if it doesn't exist
            try:
                self.redis.xgroup_create(
                    stream_name, consumer_group, id="0", mkstream=True
                )
            except Exception:
                # Group already exists, that's fine
                pass

            while True:
                # Read from stream
                messages = self.redis.xreadgroup(
                    consumer_group,
                    consumer_name,
                    {stream_name: ">"},
                    count=1,
                    block=block,
                )

                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        try:
                            # Parse event
                            event_json = fields[b"event"].decode("utf-8")
                            event = json.loads(event_json)

                            # Process event with retry logic
                            success = self._process_with_retry(
                                handler, event, max_retries=3
                            )

                            if success:
                                # Acknowledge message
                                self.redis.xack(
                                    stream_name, consumer_group, msg_id)
                                logger.info(
                                    f"Processed event {event.get('event_id')} "
                                    f"from stream {stream_name}"
                                )
                            else:
                                logger.error(
                                    f"Handler failed after retries for event "
                                    f"{event.get('event_id')}. Message not acknowledged."
                                )
                                # In production, you might want to move to a dead letter queue
                        except Exception as e:
                            logger.error(
                                f"Error processing event {msg_id}: {e}",
                                exc_info=True,
                            )
                            # Don't acknowledge on error - will be retried
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
            raise


class KafkaConsumer(EventConsumer):
    """Kafka implementation of event consumer (for future use)."""

    def __init__(self, kafka_consumer):
        """
        Initialize Kafka consumer.

        Args:
            kafka_consumer: Kafka consumer instance
        """
        self.consumer = kafka_consumer

    def consume(
        self,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        handler: Callable[[Dict[str, Any]], bool],
        block: int = 1000,
    ):
        """Consume events from Kafka topic."""
        self.consumer.subscribe([stream_name])

        try:
            while True:
                msg_pack = self.consumer.poll(timeout_ms=block)

                for topic_partition, messages in msg_pack.items():
                    for message in messages:
                        try:
                            event = message.value
                            success = handler(event)

                            if success:
                                self.consumer.commit()
                                logger.info(
                                    f"Processed event {event.get('event_id')} "
                                    f"from topic {stream_name}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error processing message: {e}", exc_info=True)
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
            raise
