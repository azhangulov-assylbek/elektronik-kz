from decimal import Decimal, InvalidOperation


def parse_price(value: str | None) -> Decimal | None:
    """Цена из GET-параметра фильтра; пустое или нечисловое значение — None (фильтр не применяется).

    Без этого строка вроде ``abc`` уходила прямо в ``filter(price__gte=...)``
    и ORM падал с ValidationError (500).
    """
    if not value:
        return None
    try:
        price = Decimal(value.replace(',', '.'))
    except InvalidOperation:
        return None
    return price if price.is_finite() else None
