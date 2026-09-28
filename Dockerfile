FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Прод-сервер приложения; миграции и collectstatic выполняются при старте
# контейнера (см. command в docker-compose.yml), т.к. им нужны переменные
# окружения и тома, которых нет на этапе сборки образа.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
