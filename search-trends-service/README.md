# Search Trends Service

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-009688?logo=fastapi&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-4.0-black?logo=apachekafka)
![Redis](https://img.shields.io/badge/Redis-8-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Prometheus](https://img.shields.io/badge/Metrics-Prometheus-E6522C?logo=prometheus&logoColor=white)

Сервис на Python/FastAPI для расчёта популярных поисковых запросов за последние 5 минут —
бэкенд виджета «Сейчас ищут». HTTP API и Kafka-воркер читают поток поисковых событий,
агрегируют их в скользящем окне и хранят состояние в Redis: счётчики запросов,
идемпотентность по `event_id`, rate-лимиты по автору события и динамический стоп-лист.
Оба компонента (API и воркер) полностью stateless — всё разделяемое состояние живёт в Redis,
поэтому оба можно масштабировать горизонтально независимо друг от друга.

## Quick Start

Понадобятся Docker Desktop, Python 3.12+ и `uv`.

```bash
cp .env.example .env
# Замените ADMIN_TOKEN в .env на длинный случайный токен (минимум 16 символов).
uv sync
docker compose up --build -d
docker compose ps
```

Дождитесь, пока Redis, Kafka и API станут healthy. Kafka topic `search.events.v1`
(6 партиций) создаётся автоматически сервисом `topic-init` — вручную ничего создавать не
нужно.

Сгенерировать тестовый трафик (10 000 событий по умолчанию):

```bash
uv run python scripts/produce_events.py
```

Проверить сервис:

```bash
curl http://localhost:8000/api/v1/health/live
curl 'http://localhost:8000/api/v1/trends?limit=10'
curl http://localhost:8000/metrics
```

### Доступные адреса

| Сервис | Адрес |
| --- | --- |
| API | <http://localhost:8000> |
| OpenAPI / Swagger UI | <http://localhost:8000/docs> |
| Метрики API | <http://localhost:8000/metrics> |
| Prometheus UI | <http://localhost:9090> |
| Kafka (внешний listener) | `localhost:29092` |
| Redis | `localhost:6379` |

Метрики воркера отдаются на порту `9000`, но наружу из Docker Compose не публикуются —
их собирает Prometheus внутри сети по адресу `worker:9000`.

### Остановка

```bash
docker compose down
```

## API

### Liveness / readiness

```bash
curl http://localhost:8000/api/v1/health/live
```

Ответ: `{"status":"ok"}`. Liveness не обращается к Redis и остаётся `200`, даже если Redis
недоступен.

```bash
curl http://localhost:8000/api/v1/health/ready
```

Проверяет доступность Redis (`PING`). Если Redis недоступен — `503` с телом
`{"detail":"Redis is unavailable"}`. Тот же безопасный `503`-ответ (без деталей ошибки
подключения) возвращают `/trends` и `/stop-words` при недоступности Redis во время обработки
запроса.

### Top-N запросов

```bash
curl 'http://localhost:8000/api/v1/trends?limit=20'
```

Пример ответа:

```json
{
  "window_seconds": 300,
  "generated_at": "2026-08-01T21:00:00Z",
  "items": [
    { "query": "iphone 15", "count": 128 },
    { "query": "ноутбук", "count": 94 }
  ]
}
```

`limit` должен быть не меньше 1 (иначе `422`); значение выше `MAX_TOP_LIMIT` не считается
ошибкой, а обрезается сервисом до `MAX_TOP_LIMIT`.

### Стоп-лист (только для admin)

Все три эндпоинта требуют заголовок `X-Admin-Token`, который сверяется с `ADMIN_TOKEN` из
`.env` через constant-time сравнение. Без валидного токена — `401`.

```bash
curl -H "X-Admin-Token: $ADMIN_TOKEN" http://localhost:8000/api/v1/stop-words
```

Ответ: `{"words":["казино"]}`.

```bash
curl -X POST \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"word":"казино"}' \
  http://localhost:8000/api/v1/stop-words
```

Ответ `201`: `{"words":["казино"]}`. Слово нормализуется тем же способом, что и запросы, и
должно состоять ровно из одного токена — иначе `422`.

```bash
curl -X DELETE \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/stop-words/%D0%BA%D0%B0%D0%B7%D0%B8%D0%BD%D0%BE
```

`204 No Content`, если слово было в списке; `404`, если такого слова нет.

### Метрики

```bash
curl http://localhost:8000/metrics
```

Эндпоинт находится вне префикса `/api/v1` и отдаёт метрики API в формате Prometheus text
exposition format.

## Мониторинг

Prometheus (`prometheus/prometheus.yml`) скрейпит два таргета с интервалом 5 секунд:

- `api:8000/metrics` — латентность и размер ответа `/trends`;
- `worker:9000` — исходы обработки событий и лаг Kafka-консьюмера.

Ключевые метрики (`src/search_trends/core/metrics.py`):

| Метрика | Тип | Назначение |
| --- | --- | --- |
| `search_events_total{outcome}` | Counter | события по исходу: `accepted`, `duplicate`, `rate_limited`, `invalid`, `ignored_empty`, `ignored_stop_word`, `ignored_too_old`, `ignored_from_future` |
| `search_consumer_lag{topic,partition}` | Gauge | лаг консьюмера по партициям |
| `search_top_request_seconds` | Histogram | время построения/чтения `/trends` |
| `search_top_result_size` | Histogram | размер выдачи `/trends` |

Рекомендуемые алерты: отказ readiness-проверки, устойчивый рост `search_consumer_lag`,
всплеск `outcome="invalid"`, всплеск `outcome="rate_limited"` и p95
`search_top_request_seconds` выше продуктового SLO.

## Архитектура

```text
поисковый сервис -> Kafka (search.events.v1) -> worker(ы) -> Redis <- API (реплики) <- виджет «Сейчас ищут»
                                                       |                  |
                                                       +---> /metrics <---+---> Prometheus
```

API и воркер не хранят состояния локально и масштабируются независимо: партиции Kafka
распределяют нагрузку между воркерами, Redis — общий источник истины для всех реплик API.

### Sliding window в Redis

Принятое событие атомарно инкрементирует sorted set 10-секундного бакета
`trends:bucket:<epoch // BUCKET_SECONDS>` через `ZINCRBY`; member — нормализованный запрос,
score — счётчик. Бакеты живут `WINDOW_SECONDS + 2 * BUCKET_SECONDS` секунд и истекают сами по
TTL. Чтение `/trends` объединяет бакеты, попадающие в последние `WINDOW_SECONDS`, через
`ZUNIONSTORE` в ключ `trends:top-cache:<epoch // TOP_CACHE_SECONDS>` и кэширует результат на
`TOP_CACHE_SECONDS` (по умолчанию 1 секунда) — при повторном запросе в то же окно кэша Redis
просто отдаёт уже посчитанный union.

Запись стоит `O(log cardinality)` и никогда не сканирует всё окно; чтение переиспользует
общий кэш вместо пересчёта на каждый HTTP-запрос, что соответствует ожидаемому профилю
нагрузки (чтений на порядки больше, чем записей). Первый частично заполненный бакет на
границе окна не включается в union, поэтому у самой старой границы окна возможен пропуск до
`BUCKET_SECONDS - 1` секунд данных. Уменьшение `BUCKET_SECONDS` повышает точность границы
ценой большего числа ключей в каждом `ZUNIONSTORE`.

При чтении `/trends` результат постранично выбирается через `ZREVRANGE` (страницами по
`max(limit * 4, 100)`) и на лету фильтруется по текущему стоп-листу — благодаря этому новое
стоп-слово сразу скрывает уже накопленную статистику, без отдельного шага очистки.

### Dynamic stop-list

Стоп-лист хранится в Redis-множестве `trends:stop-words` и управляется через admin API без
перезапуска сервиса. Он применяется дважды: на приёме события (запрос со стоп-словом не
попадает в агрегацию) и при чтении Top-N (на случай, если слово добавили после того, как
запрос уже был учтён).

## Kafka-контракт и обоснование полей

Topic: `search.events.v1`, 6 партиций, кодировка — UTF-8 JSON. Ключ сообщения — исходный
текст запроса в виде bytes (см. `scripts/produce_events.py`); поскольку агрегация идёт в
общем Redis, а не в памяти конкретного воркера, выбор ключа партиционирования влияет только
на распределение нагрузки между воркерами, а не на корректность подсчёта.

Пример payload:

```json
{
  "event_id": "7f14c59e-4c6d-4567-af04-cd989fa944ff",
  "query": "  Смартфон Samsung  ",
  "occurred_at": "2026-07-29T09:30:00Z",
  "actor_id": "hmac-session-identifier"
}
```

| Поле | Обязательное | Назначение |
| --- | --- | --- |
| `event_id` | да | UUID для идемпотентности при повторной доставке Kafka (at-least-once) |
| `query` | да | сырой поисковый запрос (1–256 символов); нормализуется воркером (NFKC, casefold, схлопывание пробелов) перед агрегацией |
| `occurred_at` | да | время поиска с обязательной таймзоной; определяет попадание события в пятиминутное окно |
| `actor_id` | да | стабильный privacy-safe идентификатор (1–128 символов), используется только для anti-fraud |

Формат зафиксирован в README, потому что схема сообщений Kafka сама по себе ничего не
навязывает продюсерам. `query` — единственное поле, по которому считается популярность,
поэтому оно обязательно и нормализуется одинаково для агрегации и для сравнения со
стоп-листом. `actor_id` обязателен, так как без стабильного идентификатора невозможно
отличить один голос от накрутки повторными событиями; сервис хеширует его (SHA-256) перед
использованием в Redis-ключах, поэтому `actor_id` должен быть уже privacy-safe значением
(например HMAC от сессии или аккаунта на стороне поискового сервиса) — сырые IP или
персональные данные передавать в этом поле нельзя. `occurred_at` обязателен для проверки
скользящего окна: события старше `WINDOW_SECONDS` или более чем на 30 секунд «из будущего»
отбрасываются ещё до обращения к Redis. `event_id` обязателен для дедупликации при
повторной доставке.

Неизвестные поля допускаются ради обратной совместимости. Некорректные сообщения (битый
JSON или невалидная схема) считаются в `search_events_total{outcome="invalid"}` и логируются
без содержимого `query`, `actor_id` или самого payload — так поток не блокируется одним
«отравленным» сообщением, а требование не логировать сырые запросы и идентификаторы
соблюдается.

## Anti-fraud

- **Идемпотентность.** `event_id` принимается один раз: ключ `trends:dedup:<event_id>`
  ставится через `SET NX EX` с TTL `WINDOW_SECONDS * 2` (10 минут при значениях по
  умолчанию). Повторная доставка того же события засчитывается как `duplicate`, а не как
  новый голос.
- **Rate-limit по автору и запросу.** Один `actor_id` может дать не более
  `MAX_EVENTS_PER_ACTOR_QUERY` (по умолчанию 30) одинаковых нормализованных запросов за
  `RATE_WINDOW_SECONDS` (по умолчанию 10 секунд); счётчик хранится с TTL
  `RATE_WINDOW_SECONDS * 2`.
- **Атомарность.** Проверка дедупликации, инкремент rate-лимита и `ZINCRBY` в бакет
  выполняются одним Lua-скриптом (`RECORD_SCRIPT`) через `EVAL` — гонки между несколькими
  воркерами, читающими один и тот же ключ, исключены.
- **Хеширование идентификаторов.** `actor_id` и `query` хешируются (SHA-256, первые 24
  hex-символа) перед тем, как попасть в ключи `trends:rate:*` — сырые значения в Redis не
  сохраняются.
- **Временное окно.** События старше `WINDOW_SECONDS` или более чем на 30 секунд из будущего
  игнорируются в `TrendService.record` до обращения к Redis.
- **Стоп-лист.** Запросы, содержащие текущее стоп-слово (по токенам), не засчитываются ни на
  запись, ни при чтении.

Ограничение: механизм основан на подсчёте уникальных `actor_id` и не защищает от атак с
большим количеством разных, но валидно выглядящих идентификаторов — это должно
компенсироваться на уровне upstream-сервиса (bot-сигналы, квоты) либо офлайн-моделями
аномалий.

## Производительность

Нагрузочное тестирование выполнялось локально через `hey` (контейнер `williamyeh/hey`),
запускаемый скриптом `scripts/benchmark.sh`.

### Окружение

- Apple Silicon MacBook, Docker Desktop.
- Один API-контейнер с одним процессом Uvicorn.
- Redis, Kafka, worker, API и Prometheus подняты через Docker Compose.
- `williamyeh/hey` выполняется под amd64-эмуляцией на arm64-хосте.
- Top-N содержал шесть заполненных запросов; размер ответа — 331 байт.

### Команда

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:29092 uv run python scripts/produce_events.py
DURATION=15s CONCURRENCY=100 ./scripts/benchmark.sh
```

### Результат (2026-08-03)

| Метрика | Значение |
| --- | ---: |
| Длительность | 15.0603 с |
| Конкурентность | 100 |
| Успешных ответов | 22 545 |
| Доля HTTP 200 | 100% |
| Throughput | 1 496.98 запросов/с |
| Средняя латентность | 66.4 мс |
| p50 латентность | 63.5 мс |
| p95 латентность | 96.4 мс |
| p99 латентность | 140.7 мс |
| Самый медленный ответ | 225.1 мс |

Сырой вывод `hey` пишется в `benchmark-results/top-n.txt` и намеренно игнорируется Git.

### Ограничения локального бенчмарка

Результаты зависят от загрузки хоста, лимитов ресурсов Docker, кардинальности ответов и
латентности Redis; `hey` под эмуляцией архитектуры на arm64-хосте дополнительно занижает
измеримый максимум. Это воспроизводимый результат для одной машины разработки, а не оценка
продакшен-ёмкости: для неё нужен представительный поток событий, продолжительные прогоны,
инъекция отказов и раздельное измерение масштабирования API и воркера. Бенчмарк с другой
машины не принимается как доказательство — для воспроизводимых цифр команду нужно запускать
на целевом хосте:

```bash
DURATION=30s CONCURRENCY=100 ./scripts/benchmark.sh
```

## Quality checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy .
docker compose config --quiet
```

Тесты (`tests/unit`, `tests/api`) покрывают: нормализацию запросов и токенизацию; бизнес-логику
`TrendService` — принятие событий, отбрасывание по стоп-слову и по границам временного окна,
проброс исходов `accepted`/`duplicate`/`rate_limited`, ранжирование Top-N; поведение воркера
на битом JSON и невалидной схеме без логирования содержимого сообщения и с коммитом офсета
мимо «отравленного» сообщения, а также на временной недоступности Redis — повтор с
exponential backoff, отсутствие коммита офсета до успешной обработки события и успешное
восстановление после реконнекта; HTTP-эндпоинты — `/trends`, обязательность admin-токена для
стоп-листа, `503` при недоступном Redis для `/health/ready`, `/trends` и `/stop-words`, при
этом `/health/live` остаётся `200`.

Тесты не зависят от `ADMIN_TOKEN`, экспортированного в shell или заданного в `.env`: `conftest.py`
принудительно переопределяет переменную окружения и сбрасывает кеш `get_settings()` до и после
каждого теста.

## Trade-offs

- **Redis как общее состояние.** Даёт stateless API и воркер, которые масштабируются
  независимо, но добавляет сетевой round-trip к каждой операции по сравнению с in-memory
  хранением и делает сервис зависимым от доступности Redis.
- **10-секундные бакеты.** `BUCKET_SECONDS` определяет одновременно и точность границы окна
  (до `BUCKET_SECONDS - 1` секунд может выпадать на краю), и число ключей, объединяемых в
  каждом `ZUNIONSTORE` (30 бакетов при значениях по умолчанию) — меньший бакет точнее, но
  дороже при чтении.
- **Кэш `/trends` на 1 секунду.** Резко снижает нагрузку на Redis от повторных чтений, но
  результат может отставать от только что записанных событий на этот интервал.
- **Постраничная фильтрация стоп-слов при чтении.** Не требует отдельного пересчёта топа при
  каждом изменении стоп-листа, но при большой доле застопленных запросов в топе может
  потребовать нескольких проходов `ZREVRANGE`.
- **Статический admin-токен.** Проверяется constant-time сравнением, но токен один общий на
  всех admin-клиентов и не даёт аудита по вызывающей стороне; для продакшена нужна сервисная
  идентичность/RBAC и аудит-лог.
- **At-least-once Kafka.** Ручной коммит офсета после обработки всего батча партиции + Lua
  дедупликация по `event_id` делают повторную доставку безопасной ценой обязательной
  идемпотентности на стороне Redis-операции.
- **Один Redis-узел в Docker Compose.** `appendonly yes` даёт персистентность на диск, но не
  защищает от потери единственного узла; для продакшена нужны репликация/кластер и отдельное
  тестирование ёмкости.
- **Anti-fraud по `actor_id`.** Простая и быстрая проверка уникальности, но бессильна против
  координированной накрутки с большим числом разных идентификаторов — нужен дополнительный
  уровень защиты выше по стеку.

## Структура проекта

```text
src/search_trends/
  api/
    routes/
      health.py        # GET /health/live, /health/ready
      stop_words.py     # admin CRUD стоп-листа
      trends.py          # GET /trends
    dependencies.py      # DI: store, TrendService, admin-авторизация
    router.py             # сборка /api/v1
  core/
    config.py              # Pydantic Settings (.env)
    logging.py              # конфигурация structlog
    metrics.py                # Prometheus-метрики
  domain/
    models.py                  # Pydantic-модели событий и ответов API
    normalization.py            # NFKC-нормализация, токенизация
  infrastructure/
    redis_store.py                # Redis: sorted sets, Lua-скрипт, стоп-лист
  services/
    trends.py                       # TrendService: бизнес-правила поверх store
  main.py                            # FastAPI app, эндпоинт /metrics
  worker.py                           # Kafka consumer

scripts/
  produce_events.py    # генератор тестовых Kafka-событий
  benchmark.sh           # нагрузочный прогон через hey в Docker

tests/
  unit/    # нормализация, TrendService, воркер
  api/     # FastAPI эндпоинты (httpx + fakeredis/моки)

prometheus/
  prometheus.yml    # scrape-конфигурация

compose.yaml
Dockerfile
Makefile
pyproject.toml
```
