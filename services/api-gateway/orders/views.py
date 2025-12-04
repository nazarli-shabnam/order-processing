"""
Order views for API Gateway.
"""
import sys
from pathlib import Path
import redis
import logging
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from uuid import uuid4
from datetime import datetime

# Add shared events to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from events.schemas import OrderCreatedEvent, ProductItem
from events.publisher import RedisStreamPublisher

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=False  # Keep bytes for Redis Streams
)

# Initialize event publisher
event_publisher = RedisStreamPublisher(redis_client)


@api_view(['POST'])
def create_order(request):
    """
    Create a new order.
    
    This endpoint:
    1. Validates the request
    2. Creates an OrderCreated event
    3. Publishes the event to the message queue
    4. Returns the order details
    """
    from .serializers import CreateOrderSerializer, OrderResponseSerializer
    from .models import Order

    serializer = CreateOrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    
    # Generate order ID
    order_id = uuid4()
    
    # Calculate total amount
    total_amount = sum(
        product['price'] * product['quantity'] 
        for product in data['products']
    )
    
    # Create event
    products = [
        ProductItem(
            product_id=str(p['product_id']),
            quantity=p['quantity'],
            price=float(p['price']),
            name=p.get('name', ''),
        )
        for p in data['products']
    ]
    
    event = OrderCreatedEvent(
        order_id=str(order_id),
        user_id=str(data['user_id']),
        products=products,
        total_amount=float(total_amount),
        shipping_address=data['shipping_address'],
        user_email=data['user_email'],
    )
    
    # Publish event
    success = event_publisher.publish(
        settings.EVENT_STREAM_NAME,
        event.to_dict()
    )
    
    if not success:
        logger.error(f"Failed to publish OrderCreated event for order {order_id}")
        return Response(
            {"error": "Failed to create order. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Store lightweight order record
    order = Order.objects.create(
        order_id=order_id,
        user_id=data['user_id'],
        status='pending',
        total_amount=total_amount,
    )
    
    logger.info(f"Created order {order_id} and published OrderCreated event")
    
    # Return response
    response_serializer = OrderResponseSerializer({
        'order_id': order.order_id,
        'status': order.status,
        'total_amount': order.total_amount,
        'created_at': order.created_at,
    })
    
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_order_status(request, order_id):
    """
    Get order status.
    
    Note: This is a simple implementation. In a real system,
    you might want to query the Order Service directly or
    use a read model.
    """
    from .models import Order
    
    try:
        order = Order.objects.get(order_id=order_id)
        from .serializers import OrderResponseSerializer
        serializer = OrderResponseSerializer({
            'order_id': order.order_id,
            'status': order.status,
            'total_amount': order.total_amount,
            'created_at': order.created_at,
        })
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response(
            {"error": "Order not found"},
            status=status.HTTP_404_NOT_FOUND
        )

