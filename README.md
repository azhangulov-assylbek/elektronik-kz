# elektronik.kz

Интернет-магазин электроники: веб-витрина на Django (сессионная авторизация)
+ REST API для внешних клиентов (DRF, JWT). Проект переведён с Laravel/WordPress
на Python/Django — 2026-08-24.

Курсовой проект выполнен по ТЗ из [docs/tz-course-project.md](docs/tz-course-project.md).

## Стек

- Python 3.13, Django 6.1, Django REST Framework, SimpleJWT, drf-spectacular
- PostgreSQL — в Docker Compose (prod), SQLite — для локальной разработки без Docker
- Русский и казахский языки интерфейса
- pytest-django, flake8, mypy (django-stubs)

## Запуск через Docker (рекомендуется)

```bash
cp .env.example .env
docker compose up --build
```

Приложение поднимется на `http://localhost:8000/`, миграции применяются
автоматически при старте контейнера `web`, база — PostgreSQL в контейнере `db`.
Контейнер `web` работает с настройками `config.settings.prod` (`DEBUG=False`).

Наполнить каталог демо-товарами (31 товар, 9 категорий, с картинками):

```bash
docker compose exec web python manage.py seed_products
```

## Настройки: development и prod

Настройки — пакет `config/settings/`:

| Модуль | БД | DEBUG | Где используется |
|---|---|---|---|
| `config.settings.development` | SQLite (`db.sqlite3`) | `True` | по умолчанию: `manage.py`, `pytest`, `mypy` |
| `config.settings.prod` | PostgreSQL (`POSTGRES_*` из окружения) | `False` | Docker Compose (`DJANGO_SETTINGS_MODULE` задан в `docker-compose.yml`) |

Общие настройки — в `config/settings/base.py`, там же подгружается `.env`.

## Запуск без Docker (локальная разработка, SQLite)

```bash
cp .env.example .env
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash); .venv\Scripts\activate на cmd
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_products   # необязательно: демо-каталог
python manage.py runserver
```

PostgreSQL для этого сценария не нужен. Если нужно проверить что-то на
реальном Postgres с хоста — `docker compose up -d db` (порт 5432 опубликован)
и запуск с `DJANGO_SETTINGS_MODULE=config.settings.prod`.

## REST API и JWT

Документация (Swagger UI): `http://localhost:8000/api/docs/`
Схема OpenAPI: `http://localhost:8000/api/schema/`

Авторизация — по email или телефону, как и на сайте:

```bash
# Регистрация
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "user@example.com", "password": "StrongPass123", "first_name": "Иван"}'

# Вход
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "user@example.com", "password": "StrongPass123"}'
# -> {"user": {...}, "access": "<JWT>", "refresh": "<JWT>"}

# Запрос с токеном
curl http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer <access>"

# Обновление access-токена
curl -X POST http://localhost:8000/api/users/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh>"}'
```

Основные ресурсы: `/api/products/` (список/деталь, фильтр по категории/цене,
поиск), `/api/products/<id>/reviews/` (отзыв — только после покупки),
`/api/cart/` (GET/POST/PATCH/DELETE), `/api/orders/` (создание из корзины,
список/деталь своих заказов, отмена через PATCH/PUT/DELETE с возвратом
остатка на склад).

## Роли: продавец и администратор

Три роли пользователя: покупатель (по умолчанию), продавец, администратор
(`users.User.role`).

- **Продавец** — карточки товаров на самом сайте: `/seller/products/`
  (список), добавление и редактирование товара через форму. Каталог общий —
  продавец может отредактировать любой товар. Ссылка «Панель продавца»
  появляется в шапке сайта после входа.
- **Администратор** — массовая загрузка каталога файлом (CSV или .xlsx)
  прямо в Django admin: кнопка «Импортировать каталог» на странице
  `/admin/products/product/`. Обязательные колонки — `name`, `sku`, `price`;
  необязательные — `category`, `brand`, `description`, `stock`, `is_active`.
  Товар ищется по артикулу (`sku`): существующий — обновится, новый —
  создастся; категория и бренд создаются автоматически по названию из файла.
  Ошибочные строки (нет цены/названия) отклоняются с указанием номера
  строки, остальные при этом импортируются.

## Модерируемый импорт каталога продавцом (`bulk_import`)

Отдельный от админского импорта пошаговый процесс для продавца — `/seller/import/`
(ссылка «Импорт каталога» в шапке):

1. Загрузка файла (CSV или .xlsx; CSV читается в UTF-8 или Windows-1251 —
   типичной кодировке выгрузок из 1С/Excel).
2. Превью первых строк и ручное сопоставление колонок файла полям товара.
3. Превью данных по маппингу; подтверждение создаёт скрытые товары
   (`is_active=False`) — в каталоге их пока не видно.
4. Загрузка картинки к каждому товару — без этого отправить на модерацию нельзя.
5. Администратор («Модерация импортов», `/seller/import/moderation/`)
   одобряет партию (товары появляются в каталоге) или отклоняет с указанием
   причины.

Каждый шаг доступен только в своём статусе импорта: после отправки на
модерацию продавец уже не может пересопоставить колонки, пересоздать товары
или поменять картинки (попытка перенаправляет на актуальный шаг или к списку).

Каждая загрузка хранится как `ImportBatch` (файл, статус, маппинг, кто и когда
загрузил/проверил), строки — `ImportRow` с построчными ошибками (например,
дубликат SKU не роняет всю партию). Добавление одного товара через
`/seller/products/add/` модерации не требует.

Тестовые аккаунты (только для разработки):
- Продавец: `seller@elektronik.kz`
- Администратор: `admin@example.com` / `admin` (тот же тестовый суперпользователь)

Пароль продавца при разворачивании создайте сами через `manage.py shell`,
например:
```python
from users.models import User
User.objects.create_user(email='seller@elektronik.kz', password='...', role=User.Role.SELLER)
```

## Тесты и линтеры

```bash
pip install -r requirements-dev.txt

pytest                 # 88 тестов: каталог, корзина, заказы, оплата, auth, API, роли, импорт
flake8 .
mypy .                 # строгий режим: все функции проекта (кроме тестов) аннотированы
```

## Переводы (i18n)

Интерфейс на русском (без префикса в URL) и казахском (`/kk/...`),
переключатель — в шапке сайта. Перевод лежит в `locale/kk/LC_MESSAGES/django.po`.

Если меняете переводимые строки в коде/шаблонах, `.po` нужно обновить и
перекомпилировать в `.mo`. Стандартный способ — GNU gettext:

```bash
python manage.py makemessages -l kk
python manage.py compilemessages
```

Если `xgettext`/`msgfmt` не установлены (как на этой машине при разработке),
`.po` можно редактировать вручную, а скомпилировать через Babel (чистый
Python, дополнительно ставится через `requirements-dev.txt`):

```bash
python -c "
from babel.messages.pofile import read_po
from babel.messages.mofile import write_mo
with open('locale/kk/LC_MESSAGES/django.po', encoding='utf-8') as f:
    catalog = read_po(f, locale='kk')
with open('locale/kk/LC_MESSAGES/django.mo', 'wb') as f:
    write_mo(f, catalog)
"
```

## Структура

Названия приложений синхронизированы с проектом группы на курсе (другой
репозиторий, ведёт наставник) — `products`/`payments`/`reviews`/`users`
совпадают, чтобы сравнение и код-ревью между проектами было проще; конкретная
реализация внутри — своя, не скопирована.

- `config/` — настройки и корневой urlconf проекта Django
- `products/` — каталог товаров (Product/Category/Brand), веб-вьюхи + `api_views.py`,
  карточки товаров продавца (`seller_views.py`), импорт каталога файлом (`catalog_import.py`)
- `users/` — пользователи (вход по email/телефону), адреса, личный кабинет
- `cart/` — корзина (гостевая на сессии + привязка к пользователю)
- `orders/` — заказы, email-уведомления, бизнес-логика в `services.py`
- `payments/` — оплата заказа (мок): `Payment` (способ/статус), `services.py:create_payment`
- `reviews/` — отзывы на товары (только после покупки)
- `bulk_import/` — пошаговый импорт каталога продавцом с модерацией администратором
- `api/` — сборка urls.py для REST API (сериализаторы и вьюхи лежат в каждом
  домене рядом с моделями — `<app>/serializers.py`, `<app>/api_views.py`)
- `locale/` — переводы интерфейса (казахский)
- `templates/` — общий `base.html`
- `import/` — рабочая папка для сырых прайс-листов поставщиков (сами файлы в git не попадают)

## Чек-лист по ТЗ

- [x] Проект запускается через Docker Compose (проверено: `db` + `web` поднимаются, миграции применяются к реальному PostgreSQL)
- [x] PostgreSQL используется (в Docker Compose / prod; локальная разработка — SQLite)
- [x] Каталог: фильтры (категория, цена), поиск, сортировка, пагинация
- [x] Страница товара: детали, отзывы (только после покупки), добавление в корзину
- [x] Корзина: управление, расчёт, проверка остатков (клиент + сервер)
- [x] Оформление заказа: создание, email, мок оплаты, валидация
- [x] Личный кабинет: регистрация (email/телефон), вход, история заказов
      (фильтр по статусу и периоду), редактирование профиля, смена пароля, адреса доставки
- [x] REST API: JWT, документация (Swagger), права доступа (только свои данные)
- [x] Админка: аналитика (выручка, топ-товары), фильтры, кастомные actions
- [x] Swagger/OpenAPI работает (`/api/docs/`)
- [x] Типизация: аннотированы все функции и методы (mypy + django-stubs, `disallow_untyped_defs`);
      докстринги у всех вьюх, API и сервисов
- [x] Линтеры (flake8, mypy) без ошибок
- [x] Тесты проходят (88 тестов, pytest-django)
- [x] Роли продавца и администратора: карточки товаров и массовая загрузка каталога файлом
- [x] Модерируемый импорт каталога продавцом (`bulk_import`)
- [x] README (этот файл)
- [x] Коммиты осмысленные, история сохранена
- [ ] Ветки `feature/...` / `develop` — пока работа идёт в `master`
- [ ] Ссылка на деплой / скринкаст — не делали, магазин пока не задеплоен
- [ ] GraphQL — не делали (опционально по ТЗ)

**ФИО и группа:** Жангулов Асылбек, группа 10

## История

Ранее проект существовал в двух параллельных версиях — заброшенный Laravel-скелет в этом репозитории и рабочий демо-магазин на WordPress/WooCommerce на хостинге. Оба варианта закрыты в пользу Django. Источник товарного ассортимента — прайс-листы поставщиков (FDCOM, Comportal, Alser, Marvel); сырые файлы складываются в папку `import/` и загружаются через импорт каталога.
