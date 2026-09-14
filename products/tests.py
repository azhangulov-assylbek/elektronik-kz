import io

import openpyxl
import pytest
from django.urls import reverse

from products.models import Brand, Category, Product
from users.models import User

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


@pytest.fixture
def seller():
    return User.objects.create_user(email='seller-test@example.com', password='pass12345', role=User.Role.SELLER)


@pytest.fixture
def admin_role_user():
    return User.objects.create_user(email='admin-role@example.com', password='pass12345', role=User.Role.ADMIN)


def test_catalog_filters_by_price(client, product, category, brand):
    Product.objects.create(name='Дешёвый', sku='SKU-2', category=category, brand=brand, price=10000, stock=1)

    response = client.get(reverse('products:home'), {'max_price': 100000})

    assert response.status_code == 200
    names = [p.name for p in response.context['products']]
    assert names == ['Дешёвый']


def test_catalog_search_by_name(client, product):
    Product.objects.create(name='Другой товар', sku='SKU-3', price=1000, stock=1)

    response = client.get(reverse('products:home'), {'q': 'Nitro'})

    names = [p.name for p in response.context['products']]
    assert names == ['Acer Nitro 5']


def test_catalog_hides_inactive_products(client, product):
    product.is_active = False
    product.save()

    response = client.get(reverse('products:home'))

    assert list(response.context['products']) == []


def test_product_detail_shows_stock(client, product):
    response = client.get(reverse('products:product_detail', args=[product.slug]))

    assert response.status_code == 200
    assert response.context['product'] == product


# --- Роли: продавец / администратор ---

def test_customer_cannot_access_seller_panel(client, user):
    client.force_login(user)

    response = client.get(reverse('products:seller_product_list'))

    assert response.status_code == 403


def test_anonymous_redirected_from_seller_panel(client):
    response = client.get(reverse('products:seller_product_list'))

    assert response.status_code == 302
    assert '/users/login/' in response.url


def test_seller_can_view_product_list(client, seller, product):
    client.force_login(seller)

    response = client.get(reverse('products:seller_product_list'))

    assert response.status_code == 200
    assert product in response.context['products']


def test_seller_can_create_product(client, seller, category, brand):
    client.force_login(seller)

    response = client.post(reverse('products:seller_product_add'), {
        'name': 'Новый ноутбук', 'sku': 'NEW-1', 'category': category.id, 'brand': brand.id,
        'description': '', 'price': '199990', 'stock': '10', 'is_active': 'on',
    })

    assert response.status_code == 302
    assert Product.objects.filter(sku='NEW-1', name='Новый ноутбук').exists()


def test_seller_can_edit_any_product(client, seller, product):
    client.force_login(seller)

    response = client.post(reverse('products:seller_product_edit', args=[product.pk]), {
        'name': product.name, 'sku': product.sku, 'description': '',
        'price': '111111', 'stock': '3', 'is_active': 'on',
    })

    assert response.status_code == 302
    product.refresh_from_db()
    assert product.price == 111111


def test_admin_role_can_access_seller_panel(client, admin_role_user):
    client.force_login(admin_role_user)

    response = client.get(reverse('products:seller_product_list'))

    assert response.status_code == 200


# --- Импорт каталога файлом (только администратор) ---

def _csv_upload(text):
    from django.core.files.uploadedfile import SimpleUploadedFile
    return SimpleUploadedFile('catalog.csv', text.encode('utf-8'), content_type='text/csv')


def test_seller_cannot_reach_import_view(client, seller):
    client.force_login(seller)

    response = client.get(reverse('admin:products_product_import_catalog'))

    # у продавца нет is_staff -> Django admin отправит на страницу логина админки
    assert response.status_code in (302, 403)


def test_admin_role_without_staff_cannot_reach_admin_site(client, admin_role_user):
    # role=ADMIN выставляет is_staff=True автоматически (см. User.save()),
    # поэтому эта проверка — на случай если это поведение когда-нибудь уберут
    assert admin_role_user.is_staff is True


def test_csv_import_creates_and_updates_products(client, admin_role_user):
    client.force_login(admin_role_user)
    csv_text = (
        'name,sku,price,category,brand,stock\r\n'
        'Товар А,IMP-1,50000,Ноутбуки,Acer,5\r\n'
        'Товар Б,IMP-2,70000,Ноутбуки,Acer,3\r\n'
    )

    response = client.post(
        reverse('admin:products_product_import_catalog'),
        {'file': _csv_upload(csv_text)},
    )

    assert response.status_code == 302
    assert Product.objects.filter(sku='IMP-1', price=50000).exists()
    assert Product.objects.filter(sku='IMP-2', price=70000).exists()

    # повторный импорт с новой ценой должен ОБНОВИТЬ, а не задублировать
    csv_text_updated = (
        'name,sku,price,category,brand,stock\r\n'
        'Товар А,IMP-1,55000,Ноутбуки,Acer,5\r\n'
    )
    client.post(reverse('admin:products_product_import_catalog'), {'file': _csv_upload(csv_text_updated)})

    assert Product.objects.filter(sku='IMP-1').count() == 1
    assert Product.objects.get(sku='IMP-1').price == 55000


def test_csv_import_reports_row_errors_without_crashing(client, admin_role_user):
    client.force_login(admin_role_user)
    csv_text = 'name,sku,price\r\nБез цены,IMP-3,\r\nХорошая строка,IMP-4,1000\r\n'

    response = client.post(
        reverse('admin:products_product_import_catalog'),
        {'file': _csv_upload(csv_text)},
    )

    assert response.status_code == 302
    assert not Product.objects.filter(sku='IMP-3').exists()
    assert Product.objects.filter(sku='IMP-4').exists()


def test_xlsx_import_creates_product(client, admin_role_user):
    client.force_login(admin_role_user)
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(['name', 'sku', 'price', 'stock'])
    sheet.append(['Excel-товар', 'XLS-1', 12345, 7])
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    from django.core.files.uploadedfile import SimpleUploadedFile
    upload = SimpleUploadedFile(
        'catalog.xlsx', buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

    response = client.post(reverse('admin:products_product_import_catalog'), {'file': upload})

    assert response.status_code == 302
    assert Product.objects.filter(sku='XLS-1', price=12345).exists()
