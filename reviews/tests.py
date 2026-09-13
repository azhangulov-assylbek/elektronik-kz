import pytest
from django.urls import reverse

from orders.models import Order, OrderItem
from products.models import Category, Product
from users.models import User

from .models import Review

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return Category.objects.create(name='Ноутбуки')


@pytest.fixture
def product(category):
    return Product.objects.create(name='Acer Nitro 5', sku='SKU-1', category=category, price=459990, stock=5)


@pytest.fixture
def user():
    return User.objects.create_user(email='buyer@example.com', password='pass12345')


def test_review_rejected_without_purchase(client, user, product):
    client.force_login(user)

    response = client.post(
        reverse('reviews:add_review', args=[product.slug]),
        {'rating': 5, 'comment': 'Отлично'},
    )

    assert response.status_code == 302
    assert Review.objects.count() == 0


def test_review_allowed_after_purchase(client, user, product):
    order = Order.objects.create(
        user=user, full_name='Тест', phone='+77001234567',
        city='Алматы', street='Абая', house='1',
    )
    OrderItem.objects.create(
        order=order, product=product, product_name=product.name,
        price=product.price, quantity=1,
    )
    client.force_login(user)

    response = client.post(
        reverse('reviews:add_review', args=[product.slug]),
        {'rating': 5, 'comment': 'Отлично'},
    )

    assert response.status_code == 302
    assert Review.objects.filter(product=product, user=user, rating=5).exists()


def test_duplicate_review_rejected(client, user, product):
    Review.objects.create(product=product, user=user, rating=4, comment='Норм')
    order = Order.objects.create(
        user=user, full_name='Тест', phone='+77001234567',
        city='Алматы', street='Абая', house='1',
    )
    OrderItem.objects.create(
        order=order, product=product, product_name=product.name,
        price=product.price, quantity=1,
    )
    client.force_login(user)

    client.post(reverse('reviews:add_review', args=[product.slug]), {'rating': 1, 'comment': 'ещё раз'})

    assert Review.objects.filter(product=product, user=user).count() == 1
