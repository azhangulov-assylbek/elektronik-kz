import pytest
from django.urls import reverse

from orders.models import Order
from products.models import Product
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def product():
    return Product.objects.create(name='Acer Nitro 5', sku='SKU-1', price=459990, stock=3)


def test_register_returns_jwt_tokens(client):
    response = client.post(
        reverse('api-register'),
        {'identifier': 'api@example.com', 'password': 'StrongPass123'},
        content_type='application/json',
    )

    assert response.status_code == 201
    assert 'access' in response.json()
    assert 'refresh' in response.json()


def test_login_returns_jwt_tokens(client):
    User.objects.create_user(email='api@example.com', password='StrongPass123')

    response = client.post(
        reverse('api-login'),
        {'identifier': 'api@example.com', 'password': 'StrongPass123'},
        content_type='application/json',
    )

    assert response.status_code == 200
    assert 'access' in response.json()


def test_login_by_phone_returns_jwt(client):
    User.objects.create_user(phone='+77001234567', password='StrongPass123')

    response = client.post(
        reverse('api-login'),
        {'identifier': '+77001234567', 'password': 'StrongPass123'},
        content_type='application/json',
    )

    assert response.status_code == 200


def test_login_wrong_password_returns_401(client):
    User.objects.create_user(email='api@example.com', password='StrongPass123')

    response = client.post(
        reverse('api-login'),
        {'identifier': 'api@example.com', 'password': 'wrong'},
        content_type='application/json',
    )

    assert response.status_code == 401


def test_product_list_is_public(client, product):
    response = client.get(reverse('product-list'))

    assert response.status_code == 200
    assert response.json()['count'] == 1


def test_cart_requires_authentication(client):
    response = client.get(reverse('api-cart'))

    assert response.status_code == 401


def _auth_client(client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    token = str(RefreshToken.for_user(user).access_token)
    client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    return client


def test_add_to_cart_and_create_order_via_api(client, product):
    user = User.objects.create_user(email='api@example.com', password='StrongPass123')
    _auth_client(client, user)

    add_response = client.post(
        reverse('api-cart'), {'product': product.id, 'quantity': 2}, content_type='application/json',
    )
    assert add_response.status_code == 201

    order_response = client.post(
        reverse('order-list'),
        {
            'full_name': 'Тест', 'phone': '+77001234567', 'city': 'Алматы',
            'street': 'Абая', 'house': '1', 'payment_method': 'cash',
        },
        content_type='application/json',
    )

    assert order_response.status_code == 201
    product.refresh_from_db()
    assert product.stock == 1


def test_order_create_blocks_insufficient_stock(client, product):
    from cart.models import Cart, CartItem

    user = User.objects.create_user(email='api@example.com', password='StrongPass123')
    _auth_client(client, user)
    # Кладём в корзину больше, чем есть на складе, — так может случиться,
    # если остаток уменьшился уже после того, как товар лежит в корзине.
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=product.stock + 1)

    response = client.post(
        reverse('order-list'),
        {
            'full_name': 'Тест', 'phone': '+77001234567', 'city': 'Алматы',
            'street': 'Абая', 'house': '1', 'payment_method': 'cash',
        },
        content_type='application/json',
    )

    assert response.status_code == 400


def test_review_requires_purchase_via_api(client, product):
    user = User.objects.create_user(email='api@example.com', password='StrongPass123')
    _auth_client(client, user)

    response = client.post(
        reverse('api-product-reviews', args=[product.id]),
        {'rating': 5, 'comment': 'Отлично'},
        content_type='application/json',
    )

    assert response.status_code == 403


def test_review_for_missing_product_returns_404(client):
    user = User.objects.create_user(email='api@example.com', password='StrongPass123')
    _auth_client(client, user)

    response = client.post(
        reverse('api-product-reviews', args=[999999]),
        {'rating': 5, 'comment': 'Отлично'},
        content_type='application/json',
    )

    assert response.status_code == 404


def test_cart_json_array_body_is_not_server_error(client, product):
    user = User.objects.create_user(email='api@example.com', password='StrongPass123')
    _auth_client(client, user)

    response = client.post(reverse('api-cart'), [product.id], content_type='application/json')

    assert response.status_code == 404


def test_cancel_order_via_api_restocks(client, product):
    user = User.objects.create_user(email='api@example.com', password='StrongPass123')
    _auth_client(client, user)
    client.post(reverse('api-cart'), {'product': product.id, 'quantity': 2}, content_type='application/json')
    order_response = client.post(
        reverse('order-list'),
        {
            'full_name': 'Тест', 'phone': '+77001234567', 'city': 'Алматы',
            'street': 'Абая', 'house': '1', 'payment_method': 'cash',
        },
        content_type='application/json',
    )
    order_id = order_response.json()['id']

    cancel_response = client.delete(reverse('order-detail', args=[order_id]))

    assert cancel_response.status_code == 200
    assert cancel_response.json()['status'] == Order.Status.CANCELLED
    product.refresh_from_db()
    assert product.stock == 3
