from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import Cart


@receiver(user_logged_in)
def merge_session_cart(sender, request, user, **kwargs):
    session_key = request.session.session_key
    if not session_key:
        return
    try:
        guest_cart = Cart.objects.get(session_key=session_key, user=None)
    except Cart.DoesNotExist:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)
    user_cart.merge_from(guest_cart)
