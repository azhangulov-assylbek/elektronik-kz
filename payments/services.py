from django.utils import timezone

from orders.models import Order

from .models import Payment


def create_payment(order: Order, method: str) -> Payment:
    """Создаёт запись оплаты для заказа. Мок: картой — оплата проходит сразу."""
    payment = Payment.objects.create(order=order, method=method)
    if method == Payment.Method.CARD:
        payment.status = Payment.Status.PAID
        payment.paid_at = timezone.now()
        payment.save(update_fields=['status', 'paid_at'])
        order.status = Order.Status.PAID
        order.save(update_fields=['status'])
    return payment
