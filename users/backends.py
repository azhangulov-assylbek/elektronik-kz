from typing import Any

from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.http import HttpRequest

from .models import User


class EmailOrPhoneBackend(ModelBackend):
    """Аутентификация по email (без учёта регистра) или по телефону в формате +7XXXXXXXXXX."""

    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        if not username or not password:
            return None
        try:
            user = User.objects.get(Q(email__iexact=username) | Q(phone=username))
        except User.DoesNotExist:
            # Хешируем пароль впустую, чтобы время ответа не выдавало, существует ли пользователь.
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
