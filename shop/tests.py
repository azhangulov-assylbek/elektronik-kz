import pytest
from django.urls import reverse

from accounts.models import User
from orders.models import Order, OrderItem
from shop.models import Brand, Category, Product, Review

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return Category.objects.create(name='Ноутбуки')


@pytest.fixture
def brand():
    return Brand.objects.create(name='Acer')


@pytest.fixture
def product(category, brand):
    return Product.objects.create(
        name='Acer Nitro 5', sku='SKU-1', category=category, brand=brand,
        price=459990, stock=5,
    )


@pytest.fixture
def user():
    return User.objects.create_user(email='buyer@example.com', password='pass12345')


def test_catalog_filters_by_price(client, product, category, brand):
    Product.objects.create(name='Дешёвый', sku='SKU-2', category=category, brand=brand, price=10000, stock=1)

    response = client.get(reverse('shop:home'), {'price_max': 100000})

    assert response.status_code == 200
    names = [p.name for p in response.context['products']]
    assert names == ['Дешёвый']


def test_catalog_search_by_name(client, product):
    Product.objects.create(name='Другой товар', sku='SKU-3', price=1000, stock=1)

    response = client.get(reverse('shop:home'), {'q': 'Nitro'})

    names = [p.name for p in response.context['products']]
    assert names == ['Acer Nitro 5']


def test_catalog_hides_inactive_products(client, product):
    product.is_active = False
    product.save()

    response = client.get(reverse('shop:home'))

    assert list(response.context['products']) == []


def test_product_detail_shows_stock(client, product):
    response = client.get(reverse('shop:product_detail', args=[product.slug]))

    assert response.status_code == 200
    assert response.context['product'] == product


def test_review_rejected_without_purchase(client, user, product):
    client.force_login(user)

    response = client.post(
        reverse('shop:add_review', args=[product.slug]),
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
        reverse('shop:add_review', args=[product.slug]),
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

    client.post(reverse('shop:add_review', args=[product.slug]), {'rating': 1, 'comment': 'ещё раз'})

    assert Review.objects.filter(product=product, user=user).count() == 1
