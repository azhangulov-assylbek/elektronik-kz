from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from shop.models import Product

from .models import CartItem
from .utils import get_cart


def cart_detail(request):
    cart = get_cart(request)
    return render(request, 'cart/cart.html', {'cart': cart})


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = get_cart(request)
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except ValueError:
        quantity = 1

    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
    if not created:
        item.quantity += quantity
        item.save(update_fields=['quantity'])
    messages.success(request, f'«{product.name}» добавлен в корзину')
    return redirect('cart:detail')


@require_POST
def update_cart_item(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = item.quantity

    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save(update_fields=['quantity'])
    return redirect('cart:detail')


@require_POST
def remove_from_cart(request, item_id):
    cart = get_cart(request)
    get_object_or_404(CartItem, pk=item_id, cart=cart).delete()
    return redirect('cart:detail')
