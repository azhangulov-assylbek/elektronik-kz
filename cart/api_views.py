"""REST API корзины: /api/cart/ (GET, POST, PATCH, DELETE)."""
from collections.abc import Mapping
from typing import Any

from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product

from .models import CartItem
from .serializers import CartSerializer
from .utils import get_cart


def _payload(request: Request) -> Mapping[str, Any]:
    """Тело запроса как словарь; JSON-массив или другой не-объект считается пустым телом (а не 500)."""
    return request.data if isinstance(request.data, Mapping) else {}


class CartView(APIView):
    """Корзина текущего пользователя. Количество ограничивается остатком на складе."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Содержимое корзины."""
        return Response(CartSerializer(get_cart(request)).data)

    def post(self, request: Request) -> Response:
        """Добавить товар: ``{"product": <id>, "quantity": <n>}``."""
        data = _payload(request)
        product_id = data.get('product')
        product = Product.objects.active().filter(pk=product_id).first() if product_id is not None else None
        if not product:
            return Response({'detail': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)
        try:
            quantity = max(1, int(data.get('quantity', 1)))
        except (TypeError, ValueError):
            quantity = 1

        cart = get_cart(request)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
        desired = min(item.quantity + quantity, product.stock)
        if desired <= 0:
            item.delete()
        else:
            item.quantity = desired
            item.save(update_fields=['quantity'])
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    def patch(self, request: Request) -> Response:
        """Изменить количество: ``{"item_id": <id>, "quantity": <n>}``; 0 — удалить позицию."""
        data = _payload(request)
        cart = get_cart(request)
        item_id = data.get('item_id')
        item = cart.items.filter(pk=item_id).first() if item_id is not None else None
        if not item:
            return Response({'detail': 'Позиция не найдена'}, status=status.HTTP_404_NOT_FOUND)
        try:
            quantity = int(data.get('quantity', item.quantity))
        except (TypeError, ValueError):
            return Response({'detail': 'Некорректное количество'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            item.delete()
        else:
            item.quantity = min(quantity, item.product.stock)
            item.save(update_fields=['quantity'])
        return Response(CartSerializer(cart).data)

    def delete(self, request: Request) -> Response:
        """Удалить позицию (``{"item_id": <id>}``) или очистить всю корзину, если item_id не передан."""
        cart = get_cart(request)
        item_id = _payload(request).get('item_id')
        if item_id:
            cart.items.filter(pk=item_id).delete()
        else:
            cart.items.all().delete()
        return Response(CartSerializer(cart).data)
