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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(CartSerializer(get_cart(request)).data)

    def post(self, request):
        data = _payload(request)
        product = Product.objects.active().filter(pk=data.get('product')).first()
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

    def patch(self, request):
        data = _payload(request)
        cart = get_cart(request)
        item = cart.items.filter(pk=data.get('item_id')).first()
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

    def delete(self, request):
        cart = get_cart(request)
        item_id = _payload(request).get('item_id')
        if item_id:
            cart.items.filter(pk=item_id).delete()
        else:
            cart.items.all().delete()
        return Response(CartSerializer(cart).data)
