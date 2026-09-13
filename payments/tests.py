import pytest

from orders.models import Order
from products.models import Product
from users.models import User

from .models import Payment
from .services import create_payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def order():
    user = User.objects.create_user(email='payer@example.com', password='pass12345')
    product = Product.objects.create(name='Acer Nitro 5', sku='SKU-PAY-1', price=459990, stock=3)
    return Order.objects.create(
        user=user, full_name='Тест', phone='+77001234567',
        city='Алматы', street='Абая', house='1',
    ), product


def test_card_payment_marks_order_and_payment_paid(order):
    order_obj, _ = order

    payment = create_payment(order_obj, Payment.Method.CARD)

    order_obj.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.paid_at is not None
    assert order_obj.status == Order.Status.PAID


def test_cash_payment_stays_pending(order):
    order_obj, _ = order

    payment = create_payment(order_obj, Payment.Method.CASH)

    order_obj.refresh_from_db()
    assert payment.status == Payment.Status.PENDING
    assert payment.paid_at is None
    assert order_obj.status == Order.Status.NEW
