"""Веб-вьюхи заказов: оформление (checkout), история и детали заказа."""
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils.translation import gettext

from cart.utils import get_cart
from users.types import AuthenticatedHttpRequest

from .emails import send_order_notifications
from .forms import CheckoutForm
from .models import Order
from .services import InsufficientStockError, create_order_from_cart


@login_required
def checkout(request: AuthenticatedHttpRequest) -> HttpResponse:
    """Оформление заказа из корзины; форма предзаполняется адресом по умолчанию.

    При нехватке остатка заказ не создаётся, пользователь возвращается в корзину с сообщением.
    """
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


def _parse_date_param(value: str) -> date | None:
    """Разобрать дату YYYY-MM-DD из GET-параметра; невалидная дата молча игнорируется, как и в фильтре каталога."""
    try:
        return parse_date(value)
    except ValueError:
        return None


@login_required
def order_list(request: AuthenticatedHttpRequest) -> HttpResponse:
    """История заказов пользователя с фильтром по статусу и периоду (?status=&date_from=&date_to=)."""
    orders = Order.objects.filter(user=request.user).prefetch_related('items')

    status = request.GET.get('status', '')
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    else:
        status = ''

    date_from = _parse_date_param(request.GET.get('date_from', ''))
    date_to = _parse_date_param(request.GET.get('date_to', ''))
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)

    ctx = {
        'orders': orders,
        'statuses': Order.Status.choices,
        'current_status': status,
        'date_from': date_from.isoformat() if date_from else '',
        'date_to': date_to.isoformat() if date_to else '',
        'is_filtered': bool(status or date_from or date_to),
    }
    return render(request, 'orders/order_list.html', ctx)


@login_required
def order_detail(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    """Детали своего заказа; чужой заказ — 404."""
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})
