from .models import Cart


def cart_badge(request):
    """Количество товаров в корзине для шапки сайта — без создания сессии/корзины впустую."""
    count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = cart.total_items
    elif request.session.session_key:
        cart = Cart.objects.filter(session_key=request.session.session_key, user=None).first()
        if cart:
            count = cart.total_items
    return {'cart_items_count': count}
