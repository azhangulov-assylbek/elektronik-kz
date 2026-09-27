import io

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from products.models import Product
from users.models import User

from .models import ImportBatch, ImportRow

pytestmark = pytest.mark.django_db


def _xlsx_upload(rows, filename='catalog.xlsx'):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return SimpleUploadedFile(
        filename, buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


def _png_upload(filename='pic.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (1, 1), 'white').save(buffer, 'PNG')
    buffer.seek(0)
    return SimpleUploadedFile(filename, buffer.read(), content_type='image/png')


@pytest.fixture
def seller():
    return User.objects.create_user(email='seller@example.com', password='pass12345', role=User.Role.SELLER)


@pytest.fixture
def admin_user():
    return User.objects.create_user(email='admin@example.com', password='pass12345', role=User.Role.ADMIN)


@pytest.fixture
def customer():
    return User.objects.create_user(email='buyer@example.com', password='pass12345')


CATALOG_ROWS = [
    ['Название', 'Артикул', 'Цена', 'Остаток', 'Категория'],
    ['Тестовый ноутбук', 'BULK-1', '199990', '5', 'Ноутбуки'],
    ['Тестовая мышь', 'BULK-2', '9990', '20', 'Периферия'],
]


def _run_upload_and_map(client, seller):
    client.force_login(seller)
    upload_response = client.post(
        reverse('bulk_import:batch_upload'), {'file': _xlsx_upload(CATALOG_ROWS)},
    )
    batch = ImportBatch.objects.get(seller=seller)
    assert upload_response.status_code == 302

    mapping_response = client.post(
        reverse('bulk_import:batch_map', args=[batch.pk]),
        {'column_0': 'name', 'column_1': 'sku', 'column_2': 'price', 'column_3': 'stock', 'column_4': 'category'},
    )
    assert mapping_response.status_code == 302
    batch.refresh_from_db()
    return batch


def test_csv_map_handles_cp1251_encoding(client, seller):
    # Реальные прайс-листы поставщиков часто в Windows-1251, не UTF-8 —
    # раньше падало с UnicodeDecodeError на этом шаге.
    csv_text = 'Название,Артикул,Цена\r\nКириллица CP1251,CP1251-1,1000\r\n'
    upload = SimpleUploadedFile('catalog.csv', csv_text.encode('cp1251'), content_type='text/csv')
    client.force_login(seller)
    client.post(reverse('bulk_import:batch_upload'), {'file': upload})
    batch = ImportBatch.objects.get(seller=seller)

    response = client.get(reverse('bulk_import:batch_map', args=[batch.pk]))

    assert response.status_code == 200
    assert 'Кириллица CP1251' in response.content.decode()


def test_upload_creates_batch_with_uploaded_status(client, seller):
    client.force_login(seller)
    response = client.post(reverse('bulk_import:batch_upload'), {'file': _xlsx_upload(CATALOG_ROWS)})

    assert response.status_code == 302
    batch = ImportBatch.objects.get(seller=seller)
    assert batch.status == ImportBatch.Status.UPLOADED


def test_mapping_creates_import_rows_from_file(client, seller):
    batch = _run_upload_and_map(client, seller)

    assert batch.status == ImportBatch.Status.MAPPED
    assert batch.rows.count() == 2
    row = batch.rows.get(row_number=1)
    assert row.raw_data == {
        'name': 'Тестовый ноутбук', 'sku': 'BULK-1', 'price': '199990', 'stock': '5', 'category': 'Ноутбуки',
    }


def test_preview_confirm_creates_draft_inactive_products(client, seller):
    batch = _run_upload_and_map(client, seller)

    response = client.post(reverse('bulk_import:batch_preview', args=[batch.pk]))

    assert response.status_code == 302
    batch.refresh_from_db()
    assert batch.status == ImportBatch.Status.IMAGES_PENDING
    assert Product.objects.filter(sku='BULK-1', is_active=False).exists()
    assert Product.objects.filter(sku='BULK-2', is_active=False).exists()


def test_draft_products_not_visible_in_catalog(client, seller):
    batch = _run_upload_and_map(client, seller)
    client.post(reverse('bulk_import:batch_preview', args=[batch.pk]))

    response = client.get(reverse('products:home'))

    names = [p.name for p in response.context['products']]
    assert 'Тестовый ноутбук' not in names


def test_duplicate_sku_reported_as_row_error(client, seller):
    Product.objects.create(name='Уже есть', sku='BULK-1', price=1000, stock=1)
    batch = _run_upload_and_map(client, seller)

    client.post(reverse('bulk_import:batch_preview', args=[batch.pk]))

    row = batch.rows.get(row_number=1)
    assert row.product is None
    assert 'BULK-1' in row.error
    # вторая строка (без конфликта) всё равно создалась
    assert Product.objects.filter(sku='BULK-2').exists()


def test_submit_blocked_without_all_images(client, seller):
    batch = _run_upload_and_map(client, seller)
    client.post(reverse('bulk_import:batch_preview', args=[batch.pk]))

    response = client.post(reverse('bulk_import:batch_submit', args=[batch.pk]))

    assert response.status_code == 302
    batch.refresh_from_db()
    assert batch.status == ImportBatch.Status.IMAGES_PENDING


def test_image_upload_then_submit_moves_to_pending_approval(client, seller):
    batch = _run_upload_and_map(client, seller)
    client.post(reverse('bulk_import:batch_preview', args=[batch.pk]))

    for row in batch.rows.filter(product__isnull=False):
        client.post(
            reverse('bulk_import:batch_image_upload', args=[batch.pk, row.pk]),
            {'image': _png_upload()},
        )

    response = client.post(reverse('bulk_import:batch_submit', args=[batch.pk]))

    assert response.status_code == 302
    batch.refresh_from_db()
    assert batch.status == ImportBatch.Status.PENDING_APPROVAL
    for row in batch.rows.filter(product__isnull=False):
        row.product.refresh_from_db()
        assert row.product.image


def _submit_full_batch(client, seller):
    batch = _run_upload_and_map(client, seller)
    client.post(reverse('bulk_import:batch_preview', args=[batch.pk]))
    for row in batch.rows.filter(product__isnull=False):
        client.post(
            reverse('bulk_import:batch_image_upload', args=[batch.pk, row.pk]),
            {'image': _png_upload()},
        )
    client.post(reverse('bulk_import:batch_submit', args=[batch.pk]))
    batch.refresh_from_db()
    return batch


def test_admin_approves_batch_publishes_products(client, seller, admin_user):
    batch = _submit_full_batch(client, seller)

    client.force_login(admin_user)
    response = client.post(reverse('bulk_import:moderation_detail', args=[batch.pk]), {'action': 'approve'})

    assert response.status_code == 302
    batch.refresh_from_db()
    assert batch.status == ImportBatch.Status.APPROVED
    assert batch.reviewed_by == admin_user
    assert Product.objects.filter(sku='BULK-1', is_active=True).exists()
    assert Product.objects.filter(sku='BULK-2', is_active=True).exists()


def test_admin_rejects_batch_keeps_products_hidden(client, seller, admin_user):
    batch = _submit_full_batch(client, seller)

    client.force_login(admin_user)
    response = client.post(
        reverse('bulk_import:moderation_detail', args=[batch.pk]),
        {'action': 'reject', 'rejection_reason': 'Некорректные цены'},
    )

    assert response.status_code == 302
    batch.refresh_from_db()
    assert batch.status == ImportBatch.Status.REJECTED
    assert batch.rejection_reason == 'Некорректные цены'
    assert not Product.objects.filter(sku='BULK-1', is_active=True).exists()


def test_moderation_unknown_action_does_not_crash(client, seller, admin_user):
    batch = _submit_full_batch(client, seller)

    client.force_login(admin_user)
    response = client.post(reverse('bulk_import:moderation_detail', args=[batch.pk]), {'action': 'bogus'})

    assert response.status_code == 200
    batch.refresh_from_db()
    assert batch.status == ImportBatch.Status.PENDING_APPROVAL


def test_customer_cannot_access_import_upload(client, customer):
    client.force_login(customer)

    response = client.get(reverse('bulk_import:batch_upload'))

    assert response.status_code == 403


def test_seller_cannot_access_moderation(client, seller):
    client.force_login(seller)

    response = client.get(reverse('bulk_import:moderation_list'))

    assert response.status_code == 403


def test_anonymous_redirected_from_upload(client):
    response = client.get(reverse('bulk_import:batch_upload'))

    assert response.status_code == 302
    assert '/users/login/' in response.url


def test_single_product_add_does_not_require_admin_approval(client, seller):
    client.force_login(seller)

    response = client.post(reverse('products:seller_product_add'), {
        'name': 'Одиночный товар', 'sku': 'SINGLE-1', 'description': '',
        'price': '50000', 'stock': '2', 'is_active': 'on',
    })

    assert response.status_code == 302
    product = Product.objects.get(sku='SINGLE-1')
    assert product.is_active is True


def test_batch_isolated_between_sellers(client, seller):
    other_seller = User.objects.create_user(email='other@example.com', password='pass12345', role=User.Role.SELLER)
    client.force_login(other_seller)
    other_batch = ImportBatch.objects.create(seller=seller, file=_xlsx_upload(CATALOG_ROWS))

    response = client.get(reverse('bulk_import:batch_map', args=[other_batch.pk]))

    assert response.status_code == 404


def test_preview_paginates_at_20_rows_per_page(client, seller):
    rows = [['Название', 'Артикул', 'Цена']] + [[f'Товар {i}', f'PAGE-{i}', '1000'] for i in range(1, 26)]
    client.force_login(seller)
    client.post(reverse('bulk_import:batch_upload'), {'file': _xlsx_upload(rows)})
    batch = ImportBatch.objects.get(seller=seller)
    client.post(
        reverse('bulk_import:batch_map', args=[batch.pk]),
        {'column_0': 'name', 'column_1': 'sku', 'column_2': 'price'},
    )
    assert batch.rows.count() == 25

    page1 = client.get(reverse('bulk_import:batch_preview', args=[batch.pk]))
    page2 = client.get(reverse('bulk_import:batch_preview', args=[batch.pk]), {'page': 2})

    assert page1.context['page_obj'].paginator.num_pages == 2
    assert len(page1.context['rows_with_values']) == 20
    assert len(page2.context['rows_with_values']) == 5


def test_images_step_paginates_at_20_rows_per_page(client, seller):
    rows = [['Название', 'Артикул', 'Цена']] + [[f'Товар {i}', f'IMGPAGE-{i}', '1000'] for i in range(1, 26)]
    client.force_login(seller)
    client.post(reverse('bulk_import:batch_upload'), {'file': _xlsx_upload(rows)})
    batch = ImportBatch.objects.get(seller=seller)
    client.post(
        reverse('bulk_import:batch_map', args=[batch.pk]),
        {'column_0': 'name', 'column_1': 'sku', 'column_2': 'price'},
    )
    client.post(reverse('bulk_import:batch_preview', args=[batch.pk]))

    page1 = client.get(reverse('bulk_import:batch_images', args=[batch.pk]))

    assert page1.context['page_obj'].paginator.count == 25
    assert len(page1.context['page_obj']) == 20


def test_remap_after_wrong_mapping_rebuilds_rows(client, seller):
    batch = _run_upload_and_map(client, seller)
    # сопоставили правильно, но по сценарию продавец передумал/ошибся —
    # возвращается на шаг сопоставления и меняет его
    response = client.get(reverse('bulk_import:batch_map', args=[batch.pk]))
    assert response.status_code == 200

    remap_response = client.post(
        reverse('bulk_import:batch_map', args=[batch.pk]),
        # теперь sku и name перепутаны местами
        {'column_0': 'sku', 'column_1': 'name', 'column_2': 'price', 'column_3': 'stock', 'column_4': 'category'},
    )
    assert remap_response.status_code == 302
    assert batch.rows.count() == 2  # старые строки не задвоились

    row = batch.rows.get(row_number=1)
    assert row.raw_data['sku'] == 'Тестовый ноутбук'  # маппинг реально применился заново
    assert row.raw_data['name'] == 'BULK-1'


def test_batch_preview_has_link_back_to_mapping(client, seller):
    batch = _run_upload_and_map(client, seller)

    response = client.get(reverse('bulk_import:batch_preview', args=[batch.pk]))

    assert reverse('bulk_import:batch_map', args=[batch.pk]) in response.content.decode()


def test_import_row_str_and_batch_str():
    batch = ImportBatch(id=1, status=ImportBatch.Status.UPLOADED)
    row = ImportRow(batch_id=1, row_number=3)
    assert 'Импорт #1' in str(batch)
    assert 'Строка 3' in str(row)


MAPPING_POST = {
    'column_0': 'name', 'column_1': 'sku', 'column_2': 'price', 'column_3': 'stock', 'column_4': 'category',
}


def _step_requests(batch):
    """(url, данные POST) для каждого шага продавца."""
    row = batch.rows.filter(product__isnull=False).first()
    return [
        (reverse('bulk_import:batch_map', args=[batch.pk]), MAPPING_POST),
        (reverse('bulk_import:batch_preview', args=[batch.pk]), {}),
        (reverse('bulk_import:batch_image_upload', args=[batch.pk, row.pk]), {'image': _png_upload()}),
        (reverse('bulk_import:batch_submit', args=[batch.pk]), {}),
    ]


@pytest.mark.parametrize('final_status', [
    ImportBatch.Status.PENDING_APPROVAL,
    ImportBatch.Status.APPROVED,
    ImportBatch.Status.REJECTED,
])
def test_seller_cannot_change_batch_after_submit(client, seller, admin_user, final_status):
    batch = _submit_full_batch(client, seller)
    if final_status != ImportBatch.Status.PENDING_APPROVAL:
        client.force_login(admin_user)
        action = 'approve' if final_status == ImportBatch.Status.APPROVED else 'reject'
        client.post(reverse('bulk_import:moderation_detail', args=[batch.pk]), {'action': action})
        client.force_login(seller)
    rows_before = list(batch.rows.values_list('pk', 'product_id'))
    requests = _step_requests(batch)
    Product.objects.filter(import_rows__batch=batch).update(image='')  # чтобы заметить повторную загрузку

    for url, data in requests:
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse('bulk_import:batch_list')

    batch.refresh_from_db()
    assert batch.status == final_status
    assert list(batch.rows.values_list('pk', 'product_id')) == rows_before
    assert not Product.objects.filter(import_rows__batch=batch).exclude(image='').exists()


def test_remap_blocked_after_drafts_created(client, seller):
    batch = _run_upload_and_map(client, seller)
    client.post(reverse('bulk_import:batch_preview', args=[batch.pk]))
    rows_before = list(batch.rows.values_list('pk', 'product_id'))

    response = client.post(reverse('bulk_import:batch_map', args=[batch.pk]), MAPPING_POST)

    assert response.status_code == 302
    assert response.url == reverse('bulk_import:batch_images', args=[batch.pk])
    batch.refresh_from_db()
    assert batch.status == ImportBatch.Status.IMAGES_PENDING
    assert list(batch.rows.values_list('pk', 'product_id')) == rows_before


def test_remap_allowed_before_drafts_created(client, seller):
    batch = _run_upload_and_map(client, seller)

    response = client.post(reverse('bulk_import:batch_map', args=[batch.pk]), MAPPING_POST)

    assert response.status_code == 302
    assert response.url == reverse('bulk_import:batch_preview', args=[batch.pk])


def test_early_step_redirects_to_current_step(client, seller):
    client.force_login(seller)
    client.post(reverse('bulk_import:batch_upload'), {'file': _xlsx_upload(CATALOG_ROWS)})
    batch = ImportBatch.objects.get(seller=seller)

    response = client.get(reverse('bulk_import:batch_images', args=[batch.pk]))

    assert response.status_code == 302
    assert response.url == reverse('bulk_import:batch_map', args=[batch.pk])
