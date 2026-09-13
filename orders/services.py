from django.db import transaction
from django.db.models import F

from payments.services import create_payment
from products.models import Product

from .models import Order, OrderItem


class InsufficientStockError(Exception):
    def __init__(self, details):
        self.details = details
        super().__init__(details)


class EmptyCartError(Exception):
    pass


def create_order_from_cart(*, user, cart, order_data):
    """Атомарно создаёт заказ из корзины: проверяет остатки, списывает stock, чистит корзину."""
    with transaction.atomic():
        items = list(cart.items.select_related('product'))
        if not items:
            raise EmptyCartError

        product_ids = [item.product_id for item in items]
        locked_products = {
            p.pk: p for p in Product.objects.select_for_update().filter(pk__in=product_ids)
        }

        insufficient = [
            item for item in items
            if item.quantity > locked_products[item.product_id].stock
        ]
        if insufficient:
            raise InsufficientStockError([
                {'product': item.product.name, 'available': locked_products[item.product_id].stock}
                for item in insufficient
            ])

        order_fields = dict(order_data)
        payment_method = order_fields.pop('payment_method')

        order = Order(user=user, **order_fields)
        order.save()

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
            )
            product = locked_products[item.product_id]
            product.stock -= item.quantity
            product.save(update_fields=['stock'])

        cart.items.all().delete()
        create_payment(order, payment_method)

    return order


class OrderCannotBeCancelledError(Exception):
    pass


CANCELLABLE_STATUSES = {Order.Status.NEW, Order.Status.PAID}


def cancel_order(order):
    """Отменяет заказ и возвращает товары на склад. Разрешено только для новых/оплаченных заказов."""
    if order.status not in CANCELLABLE_STATUSES:
        raise OrderCannotBeCancelledError(order.status)

    with transaction.atomic():
        for item in order.items.all():
            Product.objects.filter(pk=item.product_id).update(stock=F('stock') + item.quantity)
        order.status = Order.Status.CANCELLED
        order.save(update_fields=['status'])

    return order
