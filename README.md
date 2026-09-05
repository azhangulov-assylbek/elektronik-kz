# elektronik.kz

Интернет-магазин электроники. Проект переведён с Laravel/WordPress на **Python (Django)** — 2026-08-24.

## Стек

- Python 3.13, Django 6.1
- PostgreSQL (через Docker Compose) / SQLite (локально без Docker)
- Русский и казахский языки интерфейса

## Запуск через Docker (рекомендуется)

```bash
cp .env.example .env
docker compose up --build
```

Приложение поднимется на `http://localhost:8000/`, миграции применяются автоматически при старте контейнера `web`.

## Запуск без Docker

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash)
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Без переменной `POSTGRES_HOST` в окружении Django автоматически использует SQLite — Postgres не обязателен для локальной разработки без Docker.

## Структура

- `config/` — настройки и корневой urlconf проекта Django
- `shop/` — каталог товаров (Product/Category/Brand)
- `accounts/` — пользователи (вход по email/телефону), адреса, личный кабинет
- `cart/` — корзина
- `orders/` — заказы

## История

Ранее проект существовал в двух параллельных версиях — заброшенный Laravel-скелет в этом репозитории и рабочий демо-магазин на WordPress/WooCommerce на хостинге. Оба варианта закрыты в пользу Django. Источник товарного ассортимента — прайс-листы поставщиков (FDCOM, Marvel), которые пока хранятся отдельно в Google Drive и ещё не подключены к проекту.
