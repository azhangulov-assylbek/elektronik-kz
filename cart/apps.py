from django.apps import AppConfig


class CartConfig(AppConfig):
    name = 'cart'

    def ready(self) -> None:
        from . import signals  # noqa: F401
