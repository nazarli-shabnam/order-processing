"""
Shared event schemas and utilities for event-driven architecture.
All services use these definitions to ensure consistency.
"""

from .schemas import (
    OrderCreatedEvent,
    OrderStatusUpdatedEvent,
    BaseEvent,
    EventType,
)
from .publisher import EventPublisher
from .consumer import EventConsumer

__all__ = [
    "OrderCreatedEvent",
    "OrderStatusUpdatedEvent",
    "BaseEvent",
    "EventType",
    "EventPublisher",
    "EventConsumer",
]

