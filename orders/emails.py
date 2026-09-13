import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Order

logger = logging.getLogger(__name__)


def send_order_notifications(order: Order) -> None:
    """Отправляет письмо покупателю и админу после оформления заказа."""
    items_text = '\n'.join(
        f'- {item.product_name} x{item.quantity} = {item.subtotal} тг.'
        for item in order.items.all()
    )
    body = (
        f'Заказ #{order.pk}\n'
        f'Получатель: {order.full_name}, {order.phone}\n'
        f'Адрес: {order.city}, {order.street}, {order.house}\n'
        f'Способ оплаты: {order.payment.get_method_display()}\n\n'
        f'{items_text}\n\n'
        f'Итого: {order.total_price} тг.'
    )

    recipients = [settings.ADMIN_EMAIL]
    if order.user.email:
        recipients.append(order.user.email)

    for recipient in recipients:
        try:
            send_mail(
                subject=f'Заказ #{order.pk} на elektronik.kz',
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except Exception:
            logger.exception('Не удалось отправить письмо о заказе #%s на %s', order.pk, recipient)
