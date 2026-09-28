from django.http import HttpRequest

from .models import User


class AuthenticatedHttpRequest(HttpRequest):
    """HttpRequest для вьюх под @login_required: ``request.user`` — всегда наш ``User``.

    Только для аннотаций типов (mypy): у обычного ``HttpRequest.user`` тип
    ``User | AnonymousUser``, хотя декоратор уже гарантирует авторизацию.
    """

    user: User
