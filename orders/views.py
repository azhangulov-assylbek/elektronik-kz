from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext

from cart.utils import get_cart

from .emails import send_order_notifications
from .forms import CheckoutForm
from .models import Order
from .services import InsufficientStockError, create_order_from_cart


@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart.items.exists():
        messages.warning(request, gettext('Ваша корзина пуста'))
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
            try:
                order = create_order_from_cart(
                    user=request.user, cart=cart, order_data=form.cleaned_data,
                )
            except InsufficientStockError as exc:
                item_tpl = gettext('%(product)s (в наличии %(available)s)')
                names = ', '.join(
                    item_tpl % {'product': d['product'], 'available': d['available']} for d in exc.details
                )
                messages.error(request, gettext('Недостаточно на складе: %(names)s') % {'names': names})
                return redirect('cart:detail')

            send_order_notifications(order)
            messages.success(request, gettext('Заказ #%(id)s оформлен') % {'id': order.pk})
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
