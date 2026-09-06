from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'price', 'quantity', 'subtotal']
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'payment_method', 'full_name', 'phone',
            'city', 'street', 'house', 'apartment', 'comment',
            'items', 'total_price', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'items', 'total_price', 'created_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'city', 'street', 'house', 'apartment', 'payment_method', 'comment']
