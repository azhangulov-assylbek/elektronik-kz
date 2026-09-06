from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from cart.utils import get_cart

from .emails import send_order_notifications
from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer
from .services import (
    EmptyCartError,
    InsufficientStockError,
    OrderCannotBeCancelledError,
    cancel_order,
    create_order_from_cart,
)


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = get_cart(request)
        try:
            order = create_order_from_cart(
                user=request.user, cart=cart, order_data=serializer.validated_data,
            )
        except EmptyCartError:
            return Response({'detail': 'Корзина пуста'}, status=status.HTTP_400_BAD_REQUEST)
        except InsufficientStockError as exc:
            return Response(
                {'detail': 'Недостаточно на складе', 'items': exc.details},
                status=status.HTTP_400_BAD_REQUEST,
            )

        send_order_notifications(order)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def _cancel(self, request, pk=None):
        order = self.get_object()
        try:
            cancel_order(order)
        except OrderCannotBeCancelledError:
            return Response(
                {'detail': f'Заказ в статусе "{order.get_status_display()}" нельзя отменить'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(OrderSerializer(order).data)

    def update(self, request, *args, **kwargs):
        return self._cancel(request, kwargs.get('pk'))

    def partial_update(self, request, *args, **kwargs):
        return self._cancel(request, kwargs.get('pk'))

    def destroy(self, request, *args, **kwargs):
        return self._cancel(request, kwargs.get('pk'))
