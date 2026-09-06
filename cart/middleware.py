class StashSessionKeyMiddleware:
    """Запоминает session_key до входа в систему.

    Django пересоздаёт session_key при login() (защита от session fixation),
    поэтому к моменту сигнала user_logged_in исходный ключ гостевой сессии
    уже недоступен через request.session.session_key. Мы сохраняем его
    заранее, чтобы cart/signals.py мог найти и слить гостевую корзину.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.pre_login_session_key = request.session.session_key
        return self.get_response(request)
