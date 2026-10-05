# Checklist — przejście z `BackgroundTasks` na Celery

> Kontekst: dziś `POST /cv/upload` (`app/api/v1/routes/ingestion.py`) odpala `CVProcessingService.process_and_store` przez FastAPI `BackgroundTasks` — działa w tym samym procesie uvicorn, bez trwałości, retry ani widoczności statusu. Ten dokument to lista rzeczy do zrobienia **przed** migracją na Celery, żeby migracja nie polegała tylko na podmianie dekoratora.
>
> Powiązane: [`roadmap.md`](./roadmap.md) Faza 4 (decyzja o kolejce), [`checklist.md`](../../checklist.md) P5.

## Kiedy w ogóle przechodzić (przypomnienie)

Sygnały, że czas na Celery:

- restart/crash procesu API w trakcie przetwarzania gubi zadanie bez śladu,
- potrzebny retry na poziomie infrastruktury (nie ręczne pętle w kodzie serwisu),
- OCR/LLM zaczyna dławić request-response w uvicorn,
- trzeba skalować przetwarzanie niezależnie od API,
- potrzebny status zadania / zadania okresowe (cleanup, re-processing).

Jeśli żaden z tych punktów nie boli — nie przechodzić jeszcze (YAGNI, Redis/broker to dodatkowy koszt operacyjny).

## Checklist — fundamenty przed Celery

### 1. Status przetwarzania w DB

- [ ] Pole `processing_status` (`pending/completed/partial/failed`) + `error_message` w modelu wyniku (`cv_structured_data` już to ma — zweryfikować, czy wystarcza).
- [ ] Migracja Alembic dla powyższego, zrobiona **przed** dotknięciem Celery, nie razem z nią.

### 2. Result/Status API

- [ ] `GET /api/v1/cv/{cv_document_id}/status`.
- [ ] `GET /api/v1/cv/{cv_document_id}/result` (404/409 dla `pending`/`failed`).
- Bez tego Celery daje trwałość zadania, ale klient API wciąż nie ma jak sprawdzić wyniku — to ma wartość już teraz, niezależnie od brokera.

### 3. Broker + result backend

- [ ] Dodać `redis` do `docker-compose.yml` (broker + result backend Celery).
- [ ] Zmienne env: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`.

### 4. Zadania przyjmują tylko dane serializowalne

- [ ] Upewnić się, że task przyjmuje `lake_record.id: UUID/int`, nie obiekty ORM/sesje.
- [ ] Zweryfikować, czy duży `raw_text` powinien być przekazywany w argumencie taska, czy odczytywany w tasku z DB po ID (unikać dużych payloadów przez broker).

### 5. Sesja DB niezależna od request scope

- [ ] `get_cv_processing_service` / serwisy muszą dać się skonstruować poza FastAPI DI — worker Celery nie ma request scope.
- [ ] Osobna sesja DB otwierana i zamykana w każdym tasku.

### 6. Idempotencja taska

- [ ] `process_and_store` nie duplikuje wpisów w DB przy retry na tym samym `lake_record.id` (upsert albo guard "już przetworzone").

### 7. Konfiguracja i obraz workera

- [ ] `celery_app.py` (broker URL, result backend, `task_serializer="json"`, retry policy).
- [ ] Nowy serwis `worker` w `docker-compose.yml` (ten sam `Dockerfile`, `command: celery -A app.celery_app worker --loglevel=info`).

### 8. Limity czasowe dla zadań LLM/OCR

- [ ] `task_time_limit` / `task_soft_time_limit`, żeby zawieszony request do Ollamy nie blokował workera w nieskończoność.

## Kolejność realizacji

1. **Punkty 1–2** (status w DB + endpointy) — samodzielna wartość, można wdrożyć dziś, bez Celery.
2. **Punkty 3, 7, 5, 4, 6, 8** — razem, jako jedna migracja na Celery, po domknięciu 1–2.

---

Odznaczaj `[x]` w miarę realizacji.
