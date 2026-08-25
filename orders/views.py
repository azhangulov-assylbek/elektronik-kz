from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from cart.utils import get_cart

from .forms import CheckoutForm
from .models import Order, OrderItem


@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart.items.exists():
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('cart:detail')

    default_address = request.user.addresses.filter(is_default=True).first()
    initial = {}
    if default_address:
        initial = {
            'full_name': request.user.get_full_name(),
            'phone': request.user.phone or '',
            'city': default_address.city,
            'street': default_address.street,
            'house': default_address.house,
            'apartment': default_address.apartment,
        }

    if request.method == 'POST':
        form = CheckoutForm(request.POST, initial=initial)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.save()
                for item in cart.items.select_related('product'):
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product.name,
                        price=item.product.price,
                        quantity=item.quantity,
                    )
                cart.items.all().delete()
            messages.success(request, f'Заказ #{order.pk} оформлен')
            return redirect('orders:detail', pk=order.pk)
    else:
        form = CheckoutForm(initial=initial)

    return render(request, 'orders/checkout.html', {'form': form, 'cart': cart})


@login_required
def order_list(request):
    orders = request.user.orders.prefetch_related('items')
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})
