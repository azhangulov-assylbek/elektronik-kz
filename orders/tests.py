from datetime import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from cart.models import CartItem
from orders.models import Order
from orders.services import (
    EmptyCartError,
    InsufficientStockError,
    OrderCannotBeCancelledError,
    cancel_order,
    create_order_from_cart,
)
from payments.models import Payment
from products.models import Product
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(email='buyer@example.com', password='pass12345')


@pytest.fixture
def product():
    return Product.objects.create(name='Acer Nitro 5', sku='SKU-1', price=459990, stock=3)


ORDER_DATA = {
    'full_name': 'Тест Тестов', 'phone': '+77001234567',
    'city': 'Алматы', 'street': 'Абая', 'house': '1',
    'payment_method': Payment.Method.CASH,
}


def _cart_with_item(user, product, quantity):
    cart = get_cart_for_user(user)
    CartItem.objects.create(cart=cart, product=product, quantity=quantity)
    return cart


def get_cart_for_user(user):
    from cart.models import Cart
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def test_create_order_decrements_stock_and_clears_cart(user, product):
    cart = _cart_with_item(user, product, 2)

    order = create_order_from_cart(user=user, cart=cart, order_data=ORDER_DATA)

    product.refresh_from_db()
    assert product.stock == 1
    assert order.items.count() == 1
    assert cart.items.count() == 0


def test_create_order_blocks_insufficient_stock(user, product):
    cart = _cart_with_item(user, product, 999)

    with pytest.raises(InsufficientStockError):
        create_order_from_cart(user=user, cart=cart, order_data=ORDER_DATA)

    product.refresh_from_db()
    assert product.stock == 3


def test_create_order_from_empty_cart_raises(user):
    cart = get_cart_for_user(user)

    with pytest.raises(EmptyCartError):
        create_order_from_cart(user=user, cart=cart, order_data=ORDER_DATA)


def test_card_payment_marks_order_paid(user, product):
    cart = _cart_with_item(user, product, 1)

    order = create_order_from_cart(
        user=user, cart=cart, order_data={**ORDER_DATA, 'payment_method': Payment.Method.CARD},
    )

    assert order.status == Order.Status.PAID


def test_cancel_order_restocks_products(user, product):
    cart = _cart_with_item(user, product, 2)
    order = create_order_from_cart(user=user, cart=cart, order_data=ORDER_DATA)

    cancel_order(order)

    product.refresh_from_db()
    order.refresh_from_db()
    assert product.stock == 3
    assert order.status == Order.Status.CANCELLED


def test_cancel_shipped_order_is_blocked(user, product):
    cart = _cart_with_item(user, product, 1)
    order = create_order_from_cart(user=user, cart=cart, order_data=ORDER_DATA)
    order.status = Order.Status.SHIPPED
    order.save(update_fields=['status'])

    with pytest.raises(OrderCannotBeCancelledError):
        cancel_order(order)


def test_checkout_view_requires_login(client, product):
    response = client.get(reverse('orders:checkout'))

    assert response.status_code == 302
    assert '/users/login/' in response.url


def test_checkout_view_creates_order(client, user, product):
    client.force_login(user)
    cart = _cart_with_item(user, product, 1)

    response = client.post(reverse('orders:checkout'), ORDER_DATA)

    order = Order.objects.get(user=user)
    assert response.status_code == 302
    assert order.items.count() == 1
    assert cart.items.count() == 0


def _order(user, status, created_at):
    order = Order.objects.create(
        user=user, full_name='Тест', phone='+77001234567', city='Алматы',
        street='Абая', house='1', status=status,
    )
    # created_at — auto_now_add, поэтому задаём дату через update().
    Order.objects.filter(pk=order.pk).update(created_at=created_at)
    return order


@pytest.fixture
def orders_history(user):
    tz = timezone.get_current_timezone()
    return {
        'old_paid': _order(user, Order.Status.PAID, datetime(2026, 1, 10, 12, tzinfo=tz)),
        'new_cancelled': _order(user, Order.Status.CANCELLED, datetime(2026, 3, 5, 12, tzinfo=tz)),
        'new_paid': _order(user, Order.Status.PAID, datetime(2026, 3, 20, 12, tzinfo=tz)),
    }


def _listed_ids(client, **params):
    response = client.get(reverse('orders:list'), params)
    assert response.status_code == 200
    return {order.pk for order in response.context['orders']}


def test_order_list_without_filters_shows_all_own_orders(client, user, orders_history):
    other = User.objects.create_user(email='other@example.com', password='pass12345')
    _order(other, Order.Status.PAID, timezone.now())
    client.force_login(user)

    assert _listed_ids(client) == {o.pk for o in orders_history.values()}


def test_order_list_filters_by_status(client, user, orders_history):
    client.force_login(user)

    ids = _listed_ids(client, status=Order.Status.PAID)

    assert ids == {orders_history['old_paid'].pk, orders_history['new_paid'].pk}


def test_order_list_filters_by_date_range(client, user, orders_history):
    client.force_login(user)

    ids = _listed_ids(client, date_from='2026-03-01', date_to='2026-03-10')

    assert ids == {orders_history['new_cancelled'].pk}


def test_order_list_ignores_invalid_filter_values(client, user, orders_history):
    client.force_login(user)

    ids = _listed_ids(client, status='nonsense', date_from='2026-02-30', date_to='abc')

    assert ids == {o.pk for o in orders_history.values()}
