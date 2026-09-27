from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class StashSessionKeyMiddleware:
    """Запоминает session_key до входа в систему.

    Django пересоздаёт session_key при login() (защита от session fixation),
    поэтому к моменту сигнала user_logged_in исходный ключ гостевой сессии
    уже недоступен через request.session.session_key. Мы сохраняем его
    заранее, чтобы cart/signals.py мог найти и слить гостевую корзину.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.pre_login_session_key = request.session.session_key  # type: ignore[attr-defined]
        return self.get_response(request)
