"""REST API заказов: /api/orders/ — создание из корзины, список/деталь своих заказов, отмена."""
from typing import Any, cast

from django.db.models import QuerySet
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from cart.utils import get_cart
from users.models import User

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
    """Заказы текущего пользователя.

    PUT/PATCH/DELETE не редактируют заказ произвольно, а отменяют его
    (с возвратом товара на склад) — только для статусов «новый»/«оплачен».
    """

    permission_classes = [permissions.IsAuthenticated]

    def _user(self) -> User:
        # IsAuthenticated гарантирует, что это не AnonymousUser.
        return cast(User, self.request.user)

    def get_queryset(self) -> QuerySet[Order]:
        return Order.objects.filter(user=self._user()).prefetch_related('items')

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Создать заказ из текущей корзины (та же логика, что и у веб-checkout)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = get_cart(request)
        try:
            order = create_order_from_cart(
                user=self._user(), cart=cart, order_data=serializer.validated_data,
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

    def _cancel(self) -> Response:
        order = self.get_object()
        try:
            cancel_order(order)
        except OrderCannotBeCancelledError:
            return Response(
                {'detail': f'Заказ в статусе "{order.get_status_display()}" нельзя отменить'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(OrderSerializer(order).data)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self._cancel()

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self._cancel()

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self._cancel()
