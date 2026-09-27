from typing import Any

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.http import HttpRequest

from users.models import User

from .models import Cart


@receiver(user_logged_in)
def merge_session_cart(sender: type[User], request: HttpRequest, user: User, **kwargs: Any) -> None:
    """При входе переносит товары из гостевой корзины в корзину пользователя."""
    # request.session.session_key меняется в auth_login() ДО отправки этого
    # сигнала (Django пересоздаёт ключ сессии при входе), поэтому берём
    # значение, сохранённое до логина — см. cart.middleware.StashSessionKeyMiddleware.
    session_key = getattr(request, 'pre_login_session_key', None)
    if not session_key:
        return
    try:
        guest_cart = Cart.objects.get(session_key=session_key, user=None)
    except Cart.DoesNotExist:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)
    user_cart.merge_from(guest_cart)
