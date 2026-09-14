import csv
import io
from decimal import Decimal, InvalidOperation

import openpyxl

from products.models import Brand, Category, Product

from .models import REQUIRED_MAPPED_FIELDS, ImportBatch, ImportRow


def parse_file(uploaded_file):
    """Возвращает (headers, rows) — сырые заголовки и строки файла (CSV/.xlsx),
    без интерпретации колонок (это отдельный шаг — сопоставление продавцом)."""
    filename = uploaded_file.name.lower()
    if filename.endswith('.xlsx'):
        workbook = openpyxl.load_workbook(uploaded_file, data_only=True)
        sheet = workbook.active
        rows_iter = sheet.iter_rows(values_only=True)
        headers = [str(cell).strip() if cell is not None else '' for cell in next(rows_iter, [])]
        rows = [list(row) for row in rows_iter if row and any(cell is not None for cell in row)]
    else:
        text = uploaded_file.read().decode('utf-8-sig')
        all_rows = list(csv.reader(io.StringIO(text)))
        headers = all_rows[0] if all_rows else []
        rows = [row for row in all_rows[1:] if any(cell.strip() for cell in row)]
    return headers, rows


def build_rows_from_mapping(batch: ImportBatch) -> None:
    """Заново читает файл батча и создаёт ImportRow по сохранённому column_mapping."""
    headers, rows = parse_file(batch.file)
    mapping = batch.column_mapping  # {'0': 'name', '2': 'price', ...}

    batch.rows.all().delete()
    import_rows = []
    for row_number, row in enumerate(rows, start=1):
        raw_data = {}
        for index_str, field_name in mapping.items():
            index = int(index_str)
            value = row[index] if index < len(row) else None
            raw_data[field_name] = '' if value is None else str(value).strip()
        import_rows.append(ImportRow(batch=batch, row_number=row_number, raw_data=raw_data))
    ImportRow.objects.bulk_create(import_rows)


def create_draft_product(row: ImportRow) -> None:
    """Создаёт черновой Product (is_active=False) из raw_data строки импорта.
    При ошибке — записывает её в row.error, товар не создаётся (строка
    просто пропускается, остальные строки батча не страдают)."""
    data = row.raw_data
    missing = REQUIRED_MAPPED_FIELDS - {k for k, v in data.items() if v}
    if missing:
        row.error = f'не заполнены обязательные поля: {", ".join(sorted(missing))}'
        row.save(update_fields=['error'])
        return

    try:
        price = Decimal(str(data['price']).replace(',', '.'))
    except InvalidOperation:
        row.error = f'некорректная цена: {data["price"]!r}'
        row.save(update_fields=['error'])
        return

    stock_raw = data.get('stock')
    try:
        stock = int(float(stock_raw)) if stock_raw else 0
    except (TypeError, ValueError):
        row.error = f'некорректный остаток: {stock_raw!r}'
        row.save(update_fields=['error'])
        return

    if Product.objects.filter(sku=data['sku']).exists():
        row.error = f'артикул уже существует в каталоге: {data["sku"]}'
        row.save(update_fields=['error'])
        return

    category = None
    if data.get('category'):
        category, _ = Category.objects.get_or_create(name=data['category'])

    brand = None
    if data.get('brand'):
        brand, _ = Brand.objects.get_or_create(name=data['brand'])

    product = Product.objects.create(
        name=data['name'],
        sku=data['sku'],
        category=category,
        brand=brand,
        description=data.get('description', ''),
        price=price,
        stock=stock,
        is_active=False,
    )
    row.product = product
    row.error = ''
    row.save(update_fields=['product', 'error'])


def create_draft_products_for_batch(batch: ImportBatch) -> None:
    for row in batch.rows.select_related('product'):
        if row.product_id is None:
            create_draft_product(row)
