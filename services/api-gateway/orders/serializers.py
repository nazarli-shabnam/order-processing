"""
Serializers for Order API.
"""
from rest_framework import serializers


class ProductItemSerializer(serializers.Serializer):
    """Product item serializer."""
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    name = serializers.CharField(required=False, allow_blank=True)


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for creating an order."""
    user_id = serializers.UUIDField()
    products = ProductItemSerializer(many=True)
    shipping_address = serializers.CharField(max_length=500)
    user_email = serializers.EmailField()

    def validate_products(self, value):
        """Validate that at least one product is provided."""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one product is required.")
        return value


class OrderResponseSerializer(serializers.Serializer):
    """Serializer for order response."""
    order_id = serializers.UUIDField()
    status = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField()

