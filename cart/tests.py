import pytest
from django.urls import reverse

from users.models import User
from cart.models import Cart, CartItem
from products.models import Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def product():
    return Product.objects.create(name='Acer Nitro 5', sku='SKU-1', price=459990, stock=3)


@pytest.fixture
def user():
    return User.objects.create_user(email='buyer@example.com', password='pass12345')


def test_add_to_cart_respects_stock(client, product):
    client.post(reverse('cart:add', args=[product.id]), {'quantity': 10})

    item = CartItem.objects.get(product=product)
    assert item.quantity == product.stock


def test_add_to_cart_accumulates_existing_quantity(client, product):
    client.post(reverse('cart:add', args=[product.id]), {'quantity': 1})
    client.post(reverse('cart:add', args=[product.id]), {'quantity': 1})

    item = CartItem.objects.get(product=product)
    assert item.quantity == 2


def test_update_cart_item_clamps_to_stock(client, product):
    client.post(reverse('cart:add', args=[product.id]), {'quantity': 1})
    item = CartItem.objects.get(product=product)

    client.post(reverse('cart:update', args=[item.id]), {'quantity': 999})

    item.refresh_from_db()
    assert item.quantity == product.stock


def test_update_cart_item_zero_removes_it(client, product):
    client.post(reverse('cart:add', args=[product.id]), {'quantity': 1})
    item = CartItem.objects.get(product=product)

    client.post(reverse('cart:update', args=[item.id]), {'quantity': 0})

    assert not CartItem.objects.filter(pk=item.pk).exists()


def test_guest_cart_merges_into_user_cart_on_login(client, user, product):
    # Реальный POST на /users/login/, а не client.force_login() — тот
    # создаёт синтетический request в обход middleware и не пройдёт через
    # StashSessionKeyMiddleware, из-за которого и работает слияние корзин.
    client.post(reverse('cart:add', args=[product.id]), {'quantity': 2})
    session_key = client.session.session_key
    guest_cart = Cart.objects.get(session_key=session_key)
    assert guest_cart.items.count() == 1

    client.post(reverse('users:login'), {'username': user.email, 'password': 'pass12345'})

    user_cart = Cart.objects.get(user=user)
    assert user_cart.items.get(product=product).quantity == 2
    assert not Cart.objects.filter(session_key=session_key).exists()
