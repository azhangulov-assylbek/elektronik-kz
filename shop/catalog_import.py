import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

import openpyxl

from .models import Brand, Category, Product

REQUIRED_COLUMNS = {'name', 'sku', 'price'}


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    errors: list = field(default_factory=list)


def _read_rows(uploaded_file):
    """Возвращает построчно словари {колонка: значение} из CSV или .xlsx."""
    filename = uploaded_file.name.lower()
    if filename.endswith('.xlsx'):
        workbook = openpyxl.load_workbook(uploaded_file, data_only=True)
        sheet = workbook.active
        rows_iter = sheet.iter_rows(values_only=True)
        header = [str(cell).strip().lower() if cell is not None else '' for cell in next(rows_iter)]
        for row in rows_iter:
            if row is None or all(cell is None for cell in row):
                continue
            yield dict(zip(header, row))
    else:
        text = uploaded_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            yield {(key or '').strip().lower(): value for key, value in row.items()}


def import_catalog(uploaded_file) -> ImportResult:
    """Импортирует товары из CSV/.xlsx, обновляя существующие по артикулу (sku)."""
    result = ImportResult()
    rows = list(_read_rows(uploaded_file))

    if not rows:
        result.errors.append('Файл пуст или не удалось прочитать строки')
        return result

    missing_columns = REQUIRED_COLUMNS - set(rows[0].keys())
    if missing_columns:
        result.errors.append(f'В файле нет обязательных колонок: {", ".join(sorted(missing_columns))}')
        return result

    for row_number, row in enumerate(rows, start=2):  # строка 1 — заголовок
        try:
            _import_row(row, result)
        except (ValueError, InvalidOperation) as exc:
            result.errors.append(f'Строка {row_number}: {exc}')

    return result


def _import_row(row, result: ImportResult) -> None:
    name = str(row.get('name') or '').strip()
    sku = str(row.get('sku') or '').strip()
    price_raw = row.get('price')

    if not name:
        raise ValueError('не указано название (колонка name)')
    if not sku:
        raise ValueError('не указан артикул (колонка sku)')
    if price_raw in (None, ''):
        raise ValueError('не указана цена (колонка price)')

    try:
        price = Decimal(str(price_raw).replace(',', '.'))
    except InvalidOperation:
        raise ValueError(f'некорректная цена: {price_raw!r}')

    category = None
    category_name = str(row.get('category') or '').strip()
    if category_name:
        category, _ = Category.objects.get_or_create(name=category_name)

    brand = None
    brand_name = str(row.get('brand') or '').strip()
    if brand_name:
        brand, _ = Brand.objects.get_or_create(name=brand_name)

    stock_raw = row.get('stock')
    try:
        stock = int(float(stock_raw)) if stock_raw not in (None, '') else 0
    except (TypeError, ValueError):
        raise ValueError(f'некорректный остаток: {stock_raw!r}')

    is_active_raw = row.get('is_active')
    is_active = (
        True if is_active_raw in (None, '')
        else str(is_active_raw).strip().lower() not in ('0', 'false', 'нет', 'no')
    )

    _, created = Product.objects.update_or_create(
        sku=sku,
        defaults={
            'name': name,
            'category': category,
            'brand': brand,
            'description': str(row.get('description') or ''),
            'price': price,
            'stock': stock,
            'is_active': is_active,
        },
    )
    if created:
        result.created += 1
    else:
        result.updated += 1
