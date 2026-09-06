# elektronik.kz

Интернет-магазин электроники: веб-витрина на Django (сессионная авторизация)
+ REST API для внешних клиентов (DRF, JWT). Проект переведён с Laravel/WordPress
на Python/Django — 2026-08-24.

Курсовой проект выполнен по ТЗ из [docs/tz-course-project.md](docs/tz-course-project.md).

## Стек

- Python 3.13, Django 6.1, Django REST Framework, SimpleJWT, drf-spectacular
- PostgreSQL (через Docker Compose) / SQLite (локально без Docker)
- Русский и казахский языки интерфейса
- pytest-django, flake8, mypy (django-stubs)

## Запуск через Docker (рекомендуется)

```bash
cp .env.example .env
docker compose up --build
```

Приложение поднимется на `http://localhost:8000/`, миграции применяются
автоматически при старте контейнера `web`, база — PostgreSQL в контейнере `db`.

## Запуск без Docker

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash); .venv\Scripts\activate на cmd
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Без переменной `POSTGRES_HOST` в окружении Django автоматически использует
SQLite — Postgres не обязателен для локальной разработки без Docker.

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

## Тесты и линтеры

```bash
pip install -r requirements-dev.txt

pytest                 # 39 тестов: каталог, корзина, заказы, auth, API
flake8 .
mypy .
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

- `config/` — настройки и корневой urlconf проекта Django
- `shop/` — каталог товаров (Product/Category/Brand/Review), веб-вьюхи + `api_views.py`
- `accounts/` — пользователи (вход по email/телефону), адреса, личный кабинет
- `cart/` — корзина (гостевая на сессии + привязка к пользователю)
- `orders/` — заказы, мок оплаты, email-уведомления, бизнес-логика в `services.py`
- `api/` — сборка urls.py для REST API (сериализаторы и вьюхи лежат в каждом
  домене рядом с моделями — `<app>/serializers.py`, `<app>/api_views.py`)
- `locale/` — переводы интерфейса (казахский)
- `templates/` — общий `base.html`

## Чек-лист по ТЗ

- [x] Проект запускается через Docker Compose (не проверено на реальном
      Docker Desktop в среде разработки — см. `CLAUDE.md`)
- [x] PostgreSQL используется (в Docker; SQLite — фолбэк для локальной разработки)
- [x] Каталог: фильтры (категория, цена), поиск, сортировка, пагинация
- [x] Страница товара: детали, отзывы (только после покупки), добавление в корзину
- [x] Корзина: управление, расчёт, проверка остатков (клиент + сервер)
- [x] Оформление заказа: создание, email, мок оплаты, валидация
- [x] Личный кабинет: регистрация (email/телефон), вход, история заказов,
      редактирование профиля, смена пароля, адреса доставки
- [x] REST API: JWT, документация (Swagger), права доступа (только свои данные)
- [x] Админка: аналитика (выручка, топ-товары), фильтры, кастомные actions
- [x] Swagger/OpenAPI работает (`/api/docs/`)
- [x] Типизация (mypy + django-stubs) и докстринги там, где логика неочевидна
- [x] Линтер (flake8) без ошибок
- [x] Базовые тесты проходят (39 тестов, pytest-django)
- [x] README (этот файл)
- [x] Коммиты осмысленные, история сохранена
- [ ] Ссылка на деплой / скринкаст — не делали, магазин пока не задеплоен
- [ ] GraphQL — не делали (опционально по ТЗ)

**ФИО и группа:** _заполнить перед сдачей_

## История

Ранее проект существовал в двух параллельных версиях — заброшенный Laravel-скелет в этом репозитории и рабочий демо-магазин на WordPress/WooCommerce на хостинге. Оба варианта закрыты в пользу Django. Источник товарного ассортимента — прайс-листы поставщиков (FDCOM, Marvel), которые пока хранятся отдельно в Google Drive и ещё не подключены к проекту.
