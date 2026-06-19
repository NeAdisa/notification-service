# Notification Service

Сервис планирования уведомлений на **FastAPI** с PostgreSQL, Redis,
SQLAlchemy, Alembic, Pydantic v2.

## Стек

- Python 3.11
- FastAPI + Uvicorn
- Pydantic v2 + pydantic-settings
- SQLAlchemy async + asyncpg
- PostgreSQL
- Alembic
- Redis
- Pytest
- Ruff, Black, Flake8
- Docker, Docker Compose

## Архитектура

Проект построен по layered architecture:

```text
HTTP request
  -> api route
  -> service
  -> repository
  -> database
```

Структура:

```text
app/
  api/routes/       HTTP endpoints, Depends, query/path params
  core/             настройки через pydantic-settings
  db/               SQLAlchemy Base, async engine, async session
  models/           SQLAlchemy модели и enum-статусы
  schemas/          Pydantic request/response схемы
  repositories/     SQL-запросы и работа с БД
  services/         бизнес-логика
  rate_limit/       custom Redis rate limiter
  workers/          background sender loop
alembic/            миграции БД
tests/              unit-тесты
```

## Конфигурация

Пример:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/notifications_db
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_MAX=10
SENDER_INTERVAL_SECONDS=5
SENDER_BATCH_SIZE=10
NOTIFICATION_MAX_ATTEMPTS=3
ENV=local
```

`.env.example` хранится в репозитории как шаблон.

## Запуск через Docker

```bash
docker compose up --build
```

## Запуск локально

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## API

```text
POST   /notifications
GET    /notifications?limit=20&offset=0&priority=high
DELETE /notifications/{id}
GET    /health
```

`POST /notifications` создаёт уведомление со статусом `scheduled`.

`GET /notifications` поддерживает:

- `limit`;
- `offset`;
- фильтр `priority`.

`DELETE /notifications/{id}` удаляет только уведомления в статусе `scheduled`.

## Модель Notification

Основные поля:

```text
id
email
message
send_at
priority
status
attempt_count
max_attempts
last_attempt_at
sent_at
last_error
created_at
updated_at
```

Priority:

```text
low, medium, high
```

Status:

```text
scheduled, processing, sent, failed, cancelled
```

## Валидация

Pydantic-схемы проверяют:

- `email` должен быть валидным;
- `message` от 10 до 500 символов;
- `send_at` не может быть в прошлом;
- `priority` только `low`, `medium`, `high`;
- `max_attempts` от 1 до 10.

Ошибки валидации возвращаются как `422`.

## Rate Limiter

Используется Redis:

```text
rate_limit:notifications:create:{ip}
```

Алгоритм:

- на каждый `POST /notifications` выполняется `INCR`;
- при первом запросе ставится TTL 60 секунд;
- если счётчик больше `RATE_LIMIT_MAX`, возвращается `429`;
- в ответ добавляется header `Retry-After`.

По умолчанию:

```text
10 requests / 60 seconds / IP
```

## Background Sender

Фоновый sender запускается через FastAPI lifespan.

Цикл:

```text
scheduled + send_at <= now
  -> processing
  -> send
  -> sent или scheduled/failed
```

Отправка сейчас имитируется через sender abstraction. Реальный SMTP/API можно
подключить позже.

Повторные попытки:

- `attempt_count` увеличивается при попытке;
- если отправка успешна - статус `sent`;
- если ошибка и попытки остались - статус снова `scheduled`;
- если попытки закончились - статус `failed`.

Очередность обработки:

```text
high -> medium -> low -> send_at -> id
```

## Alembic

Миграции находятся в:

```text
alembic/versions/
```

Текущие миграции:

- создание таблицы `notifications`;
- добавление retry/status tracking полей.

Применение:

```bash
alembic upgrade head
```

## Тесты и качество кода

Запуск тестов:

```bash
python -m pytest
```

Проверки:

```bash
python -m ruff check .
python -m black --check .
python -m flake8 .
```

Покрыто тестами:

- валидная схема уведомления;
- короткое сообщение;
- `send_at` в прошлом;
- rate limiter under limit;
- rate limiter over limit;
- удаление `scheduled`;
- запрет удаления `sent`.
