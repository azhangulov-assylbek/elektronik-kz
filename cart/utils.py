from django.http import HttpRequest
from rest_framework.request import Request

from .models import Cart


def get_cart(request: HttpRequest | Request) -> Cart:
    """Корзина текущего посетителя: пользовательская для авторизованных, иначе — по ключу сессии.

    В отличие от cart.context_processors.cart_badge, создаёт сессию и корзину, если их ещё нет.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart
