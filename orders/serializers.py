from rest_framework import serializers

from payments.models import Payment
from payments.serializers import PaymentSerializer

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
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'payment', 'full_name', 'phone',
            'city', 'street', 'house', 'apartment', 'comment',
            'items', 'total_price', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'payment', 'items', 'total_price', 'created_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    payment_method = serializers.ChoiceField(choices=Payment.Method.choices, write_only=True)

    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'city', 'street', 'house', 'apartment', 'payment_method', 'comment']
