"""Веб-вьюхи корзины. Количество всегда ограничивается остатком на складе."""
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext
from django.views.decorators.http import require_POST

from products.models import Product

from .models import CartItem
from .utils import get_cart


def cart_detail(request: HttpRequest) -> HttpResponse:
    """Содержимое корзины (гостевой на сессии или пользовательской)."""
    cart = get_cart(request)
    return render(request, 'cart/cart.html', {'cart': cart})


@require_POST
def add_to_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    """Добавить товар (или увеличить количество); сверх остатка не добавляется — с сообщением."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = get_cart(request)
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except ValueError:
        quantity = 1

    item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
    desired = item.quantity + quantity
    if desired > product.stock:
        messages.error(
            request,
            gettext('На складе только %(stock)s шт. «%(name)s» — добавлено максимум доступное') % {
                'stock': product.stock, 'name': product.name,
            },
        )
        desired = product.stock

    if desired <= 0:
        item.delete()
    else:
        item.quantity = desired
        item.save(update_fields=['quantity'])
        messages.success(
            request,
            gettext('«%(name)s» в корзине: %(qty)s шт.') % {'name': product.name, 'qty': desired},
        )
    return redirect('cart:detail')


@require_POST
def update_cart_item(request: HttpRequest, item_id: int) -> HttpResponse:
    """Изменить количество позиции; 0 и меньше — удалить, больше остатка — урезать до остатка."""
    cart = get_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = item.quantity

    if quantity <= 0:
        item.delete()
    else:
        if quantity > item.product.stock:
            messages.error(
                request,
                gettext('На складе только %(stock)s шт. «%(name)s»') % {
                    'stock': item.product.stock, 'name': item.product.name,
                },
            )
            quantity = item.product.stock
        item.quantity = quantity
        item.save(update_fields=['quantity'])
    return redirect('cart:detail')


@require_POST
def remove_from_cart(request: HttpRequest, item_id: int) -> HttpResponse:
    """Удалить позицию из корзины."""
    cart = get_cart(request)
    get_object_or_404(CartItem, pk=item_id, cart=cart).delete()
    return redirect('cart:detail')
