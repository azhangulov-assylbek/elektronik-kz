import os
from decimal import Decimal
from typing import Any

from django.core.files import File
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from products.models import Brand, Category, Product

IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'seed_images')

CATEGORIES = [
    'Ноутбуки', 'Смартфоны', 'Планшеты', 'Телевизоры', 'Наушники',
    'Умные часы', 'Мониторы', 'Периферия', 'Аксессуары',
]

# Свободные (CC0) изображения по категориям — по одному репрезентативному
# фото/иллюстрации на категорию, лежат в seed_images/ рядом с командой.
CATEGORY_IMAGES = {
    'Ноутбуки': 'laptop.jpg',
    'Смартфоны': 'smartphone.jpg',
    'Планшеты': 'tablet.jpg',
    'Телевизоры': 'tv.jpg',
    'Наушники': 'headphones.jpg',
    'Умные часы': 'smartwatch.jpg',
    'Мониторы': 'monitor.jpg',
    'Периферия': 'peripherals.jpg',
    'Аксессуары': 'accessories.jpg',
}

BRANDS = [
    'Acer', 'ASUS', 'Lenovo', 'HP', 'Dell', 'Apple', 'Samsung', 'Xiaomi',
    'Honor', 'Huawei', 'LG', 'Sony', 'JBL', 'Logitech', 'Anker', 'Baseus',
]

# (name, sku, category, brand, price, stock, description)
PRODUCTS = [
    ('Acer Aspire 5', 'NB-ACER-ASP5', 'Ноутбуки', 'Acer', 259990, 12,
     '15.6", Intel Core i5, 8 ГБ ОЗУ, SSD 512 ГБ — универсальный ноутбук для учёбы и работы.'),
    ('Acer Nitro 5', 'NB-ACER-NTR5', 'Ноутбуки', 'Acer', 459990, 6,
     '15.6" 144 Гц, Intel Core i5, RTX 3050, 16 ГБ ОЗУ — игровой ноутбук среднего класса.'),
    ('ASUS VivoBook 15', 'NB-ASUS-VB15', 'Ноутбуки', 'ASUS', 229990, 10,
     '15.6" Full HD, AMD Ryzen 5, 8 ГБ ОЗУ, SSD 512 ГБ.'),
    ('Lenovo IdeaPad 3', 'NB-LEN-IP3', 'Ноутбуки', 'Lenovo', 199990, 15,
     '15.6", Intel Core i3, 8 ГБ ОЗУ, SSD 256 ГБ — бюджетный ноутбук на каждый день.'),
    ('HP Pavilion 15', 'NB-HP-PAV15', 'Ноутбуки', 'HP', 289990, 8,
     '15.6" Full HD, Intel Core i5, 16 ГБ ОЗУ, SSD 512 ГБ.'),
    ('Dell Inspiron 14', 'NB-DELL-INS14', 'Ноутбуки', 'Dell', 274990, 7,
     '14" Full HD, Intel Core i5, 8 ГБ ОЗУ, SSD 512 ГБ.'),
    ('Apple MacBook Air M2', 'NB-APL-MBA-M2', 'Ноутбуки', 'Apple', 649990, 5,
     '13.6" Liquid Retina, чип Apple M2, 8 ГБ ОЗУ, SSD 256 ГБ.'),

    ('Apple iPhone 15', 'SP-APL-IP15', 'Смартфоны', 'Apple', 549990, 14,
     '6.1" OLED, чип A16 Bionic, 128 ГБ, двойная камера 48+12 Мп.'),
    ('Samsung Galaxy S23', 'SP-SAM-S23', 'Смартфоны', 'Samsung', 469990, 11,
     '6.1" AMOLED 120 Гц, Snapdragon 8 Gen 2, 256 ГБ.'),
    ('Xiaomi Redmi Note 13', 'SP-XIA-RN13', 'Смартфоны', 'Xiaomi', 119990, 25,
     '6.67" AMOLED 120 Гц, 256 ГБ, камера 108 Мп — популярный бюджетник.'),
    ('Honor X9b', 'SP-HON-X9B', 'Смартфоны', 'Honor', 159990, 9,
     '6.78" AMOLED, ударопрочный корпус, 256 ГБ.'),
    ('Huawei P60', 'SP-HUA-P60', 'Смартфоны', 'Huawei', 399990, 6,
     '6.67" OLED 120 Гц, флагманская камера, 256 ГБ.'),

    ('Apple iPad 10', 'TB-APL-IPAD10', 'Планшеты', 'Apple', 249990, 10,
     '10.9" Liquid Retina, чип A14 Bionic, Wi-Fi, 64 ГБ.'),
    ('Samsung Galaxy Tab A9', 'TB-SAM-TABA9', 'Планшеты', 'Samsung', 89990, 16,
     '8.7" LCD, 64 ГБ, лёгкий планшет для дома и учёбы.'),
    ('Xiaomi Redmi Pad SE', 'TB-XIA-RPSE', 'Планшеты', 'Xiaomi', 109990, 12,
     '11" 90 Гц, 128 ГБ, большой экран по доступной цене.'),

    ('Samsung QLED 55"', 'TV-SAM-QLED55', 'Телевизоры', 'Samsung', 349990, 5,
     '55", 4K QLED, Smart TV Tizen, HDR10+.'),
    ('LG OLED 55"', 'TV-LG-OLED55', 'Телевизоры', 'LG', 499990, 4,
     '55", 4K OLED, webOS, идеальный чёрный цвет.'),
    ('Xiaomi TV A2 43"', 'TV-XIA-A2-43', 'Телевизоры', 'Xiaomi', 149990, 9,
     '43", 4K, Android TV — доступный смарт-телевизор.'),

    ('Apple AirPods Pro 2', 'HP-APL-APP2', 'Наушники', 'Apple', 129990, 20,
     'Активное шумоподавление, кейс с MagSafe.'),
    ('Sony WH-1000XM5', 'HP-SNY-WH1000XM5', 'Наушники', 'Sony', 189990, 8,
     'Накладные, лучшее шумоподавление в классе, до 30 часов работы.'),
    ('JBL Tune 510BT', 'HP-JBL-T510BT', 'Наушники', 'JBL', 24990, 30,
     'Накладные беспроводные наушники, до 40 часов работы.'),
    ('Xiaomi Redmi Buds 4', 'HP-XIA-RB4', 'Наушники', 'Xiaomi', 19990, 22,
     'Вкладыши TWS с активным шумоподавлением.'),

    ('Apple Watch SE', 'SW-APL-SE', 'Умные часы', 'Apple', 149990, 10,
     '40 мм, GPS, мониторинг здоровья и активности.'),
    ('Samsung Galaxy Watch 6', 'SW-SAM-GW6', 'Умные часы', 'Samsung', 139990, 9,
     '40 мм, AMOLED, отслеживание сна и тренировок.'),
    ('Xiaomi Mi Band 8', 'SW-XIA-MB8', 'Умные часы', 'Xiaomi', 19990, 35,
     'Фитнес-браслет, AMOLED-экран, до 16 дней автономности.'),

    ('LG UltraGear 27"', 'MN-LG-UG27', 'Мониторы', 'LG', 129990, 7,
     '27", QHD 165 Гц, IPS — для игр и работы.'),
    ('Samsung Odyssey G5', 'MN-SAM-OG5', 'Мониторы', 'Samsung', 119990, 6,
     '27", QHD 165 Гц, изогнутая матрица VA.'),

    ('Logitech MX Master 3S', 'PR-LOG-MXM3S', 'Периферия', 'Logitech', 39990, 18,
     'Беспроводная мышь для продуктивной работы, тихий клик.'),
    ('Logitech K380', 'PR-LOG-K380', 'Периферия', 'Logitech', 14990, 25,
     'Компактная Bluetooth-клавиатура, до 3 устройств одновременно.'),

    ('Anker PowerCore 20000', 'AC-ANK-PC20K', 'Аксессуары', 'Anker', 17990, 40,
     'Внешний аккумулятор 20000 мАч, быстрая зарядка.'),
    ('Baseus USB-C кабель 1м', 'AC-BAS-USBC1M', 'Аксессуары', 'Baseus', 2990, 60,
     'Кабель USB-C, поддержка быстрой зарядки до 100 Вт.'),
]


class Command(BaseCommand):
    help = (
        'Наполняет каталог моковыми категориями, брендами и товарами (для разработки/демо). '
        'На боевом сервере (DEBUG=False) — только с --force; --deactivate скрывает демо-товары.'
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--force', action='store_true',
            help=(
                'Разрешить запуск при DEBUG=False (боевой сервер): '
                'демо-товары появятся в витрине и их можно будет заказать.'
            ),
        )
        parser.add_argument(
            '--deactivate', action='store_true',
            help=(
                'Не создавать товары, а скрыть уже созданные демо-товары (is_active=False). '
                'Категории и бренды остаются.'
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options['deactivate']:
            self._deactivate()
            return

        if not settings.DEBUG and not options['force']:
            raise CommandError(
                'Это боевой сервер (DEBUG=False): демо-товары появятся в витрине с ценами и остатком, '
                'покупатели смогут их заказать. Если это осознанно (например, показ демо) — '
                'запустите с --force, а после показа скройте их: seed_products --deactivate'
            )

        categories = {}
        for name in CATEGORIES:
            category, _ = Category.objects.get_or_create(name=name)
            categories[name] = category

        brands = {}
        for name in BRANDS:
            brand, _ = Brand.objects.get_or_create(name=name)
            brands[name] = brand

        created, updated, images_attached = 0, 0, 0
        for name, sku, category_name, brand_name, price, stock, description in PRODUCTS:
            product, was_created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'category': categories[category_name],
                    'brand': brands[brand_name],
                    'price': Decimal(price),
                    'stock': stock,
                    'description': description,
                    'is_active': True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

            if not product.image:
                image_path = os.path.join(IMAGES_DIR, CATEGORY_IMAGES[category_name])
                with open(image_path, 'rb') as f:
                    product.image.save(f'{sku.lower()}.jpg', File(f), save=True)
                images_attached += 1

        self.stdout.write(self.style.SUCCESS(
            f'Готово: {len(CATEGORIES)} категорий, {len(BRANDS)} брендов, '
            f'{created} товаров создано, {updated} обновлено, '
            f'{images_attached} картинок добавлено (всего {len(PRODUCTS)}).',
        ))

    def _deactivate(self) -> None:
        """Скрыть демо-товары (по их артикулам). Не удаляет: на товар могут ссылаться заказы."""
        demo_skus = [sku for _name, sku, *_rest in PRODUCTS]
        hidden = Product.objects.filter(sku__in=demo_skus, is_active=True).update(is_active=False)
        self.stdout.write(self.style.SUCCESS(
            f'Скрыто демо-товаров: {hidden}. Категории и бренды не тронуты.',
        ))
