# elektronik.kz

Интернет-магазин электроники. Проект переведён с Laravel/WordPress на **Python (Django)** — 2026-08-24.

## Стек

- Python 3.13, Django 6.1
- SQLite для разработки

## Запуск

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash)
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Структура

- `config/` — настройки и корневой urlconf проекта Django
- `shop/` — приложение магазина (каталог, товары)

## История

Ранее проект существовал в двух параллельных версиях — заброшенный Laravel-скелет в этом репозитории и рабочий демо-магазин на WordPress/WooCommerce на хостинге. Оба варианта закрыты в пользу Django. Источник товарного ассортимента — прайс-листы поставщиков (FDCOM, Marvel), которые пока хранятся отдельно в Google Drive и ещё не подключены к проекту.
