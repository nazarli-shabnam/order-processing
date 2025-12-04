"""
Event schemas - defines the structure of all events in the system.
This ensures type safety and consistency across all services.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class EventType(str, Enum):
    """All event types in the system."""
    ORDER_CREATED = "OrderCreated"
    ORDER_STATUS_UPDATED = "OrderStatusUpdated"
    # Future events:
    # PAYMENT_PROCESSED = "PaymentProcessed"
    # INVENTORY_RESERVED = "InventoryReserved"
    # SHIPPING_CREATED = "ShippingCreated"


@dataclass
class BaseEvent:
    """Base class for all events."""
    event_type: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "1.0"
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "version": self.version,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseEvent":
        """Create event from dictionary."""
        return cls(
            event_type=data["event_type"],
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            version=data.get("version", "1.0"),
            data=data["data"],
        )


@dataclass
class ProductItem:
    """Product item in an order."""
    product_id: str
    quantity: int
    price: float
    name: Optional[str] = None


@dataclass
class OrderCreatedEvent(BaseEvent):
    """Event published when a new order is created."""
    order_id: str
    user_id: str
    products: List[ProductItem]
    total_amount: float
    shipping_address: str
    user_email: str

    def __post_init__(self):
        """Set event type after initialization."""
        self.event_type = EventType.ORDER_CREATED.value
        self.data = {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "products": [
                {
                    "product_id": p.product_id,
                    "quantity": p.quantity,
                    "price": p.price,
                    "name": p.name,
                }
                for p in self.products
            ],
            "total_amount": self.total_amount,
            "shipping_address": self.shipping_address,
            "user_email": self.user_email,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderCreatedEvent":
        """Create OrderCreatedEvent from dictionary."""
        event_data = data["data"]
        return cls(
            event_type=data["event_type"],
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            version=data.get("version", "1.0"),
            order_id=event_data["order_id"],
            user_id=event_data["user_id"],
            products=[
                ProductItem(
                    product_id=p["product_id"],
                    quantity=p["quantity"],
                    price=p["price"],
                    name=p.get("name"),
                )
                for p in event_data["products"]
            ],
            total_amount=event_data["total_amount"],
            shipping_address=event_data["shipping_address"],
            user_email=event_data["user_email"],
        )


@dataclass
class OrderStatusUpdatedEvent(BaseEvent):
    """Event published when order status changes."""
    order_id: str
    status: str  # pending, processing, completed, cancelled
    previous_status: str
    updated_at: str
    user_email: str  # User email for notifications

    def __post_init__(self):
        """Set event type after initialization."""
        self.event_type = EventType.ORDER_STATUS_UPDATED.value
        self.data = {
            "order_id": self.order_id,
            "status": self.status,
            "previous_status": self.previous_status,
            "updated_at": self.updated_at,
            "user_email": self.user_email,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderStatusUpdatedEvent":
        """Create OrderStatusUpdatedEvent from dictionary."""
        event_data = data["data"]
        return cls(
            event_type=data["event_type"],
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            version=data.get("version", "1.0"),
            order_id=event_data["order_id"],
            status=event_data["status"],
            previous_status=event_data["previous_status"],
            updated_at=event_data["updated_at"],
            user_email=event_data.get("user_email", ""),  # Backward compatible
        )
