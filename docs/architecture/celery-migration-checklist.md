# Checklist — przejście z `BackgroundTasks` na Celery

> Kontekst: dziś `POST /cv/upload` (`app/api/v1/routes/ingestion.py`) odpala `CVProcessingService.process_and_store` przez FastAPI `BackgroundTasks` — działa w tym samym procesie uvicorn, bez trwałości, retry ani widoczności statusu. Ten dokument to lista rzeczy do zrobienia **przed** migracją na Celery, żeby migracja nie polegała tylko na podmianie dekoratora.
>
> Powiązane: [`celery-roadmap.md`](./celery-roadmap.md) (kolejność PR-ów, jeśli ta checklista jest już przerobiona), [`roadmap.md`](./roadmap.md) Faza 4 (decyzja o kolejce), [`checklist.md`](../../checklist.md) P5.

## Kiedy w ogóle przechodzić (przypomnienie)

Sygnały, że czas na Celery:

- restart/crash procesu API w trakcie przetwarzania gubi zadanie bez śladu,
- potrzebny retry na poziomie infrastruktury (nie ręczne pętle w kodzie serwisu),
- OCR zaczyna dławić request-response w uvicorn,
- trzeba skalować przetwarzanie niezależnie od API,
- potrzebny status zadania / zadania okresowe (cleanup, re-processing).

Jeśli żaden z tych punktów nie boli — nie przechodzić jeszcze (YAGNI, Redis/broker to dodatkowy koszt operacyjny).

## Checklist — fundamenty przed Celery

### 1. Status przetwarzania w DB

- [x] Pole `processing_status` (`pending/completed/partial/failed`) w modelu wyniku (`cv_structured_data` już to ma — zweryfikowane, wystarcza na dzisiejszy zakres). `error_message` nie został dodany — `status="failed"` jest na razie jedynym sygnałem błędu; do rozważenia później, jeśli zajdzie potrzeba diagnozy przyczyny.
- [x] Migracja Alembic dla powyższego — nie dotyczy: tabela `cv_structured_data` istniała już przed tą migracją, a Alembic w tym repo jeszcze nie jest wdrożony (schemat tworzy `SQLModel.metadata.create_all()`) — patrz `celery-roadmap.md` Faza 5, świadomie wstrzymana do wprowadzenia Alembica/CI-CD.

### 2. Result/Status API

- [x] `GET /api/v1/cv/{cv_document_id}/structured` — łączy status i wynik w jednym endpointzie (zamiast dwóch osobnych `/status` + `/result`), zrealizowane przed tą migracją.
- [x] `GET /api/v1/cv/stats` — zliczenie dokumentów per status, dodane w Fazie 4 `celery-roadmap.md`.
- Bez tego Celery daje trwałość zadania, ale klient API wciąż nie ma jak sprawdzić wyniku — to ma wartość już teraz, niezależnie od brokera.

### 3. Broker + result backend

- [x] Dodać `redis` do `docker-compose.yml` (broker + result backend Celery).
- [x] Zmienne env: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`.

### 4. Zadania przyjmują tylko dane serializowalne

- [x] Task przyjmuje `cv_document_id: str` (UUID serializowany do stringa przed wysyłką), nie obiekty ORM/sesje.
- [x] Zweryfikowano: `raw_text` jest przekazywany w argumencie taska (tak jak wcześniej w `BackgroundTasks`) — to string, serializuje się do JSON bez problemu; odczyt z DB po ID uznany za niepotrzebną optymalizację na tym etapie.

### 5. Sesja DB niezależna od request scope

- [x] `CVProcessingService` konstruowany wprost w tasku (`CVProcessingService()`), bez FastAPI DI.
- [x] Osobna sesja DB (`Session(engine)`) otwierana i zamykana w `CVProcessingService._store`, niezależnie od request scope.

### 6. Idempotencja taska

- [x] `process_and_store` nie duplikuje wpisów w DB przy retry na tym samym `lake_record.id` (upsert albo guard "już przetworzone") — `upsert_structured_record` nadpisuje po PK `cv_document_id`, potwierdzone.

### 7. Konfiguracja i obraz workera

- [x] `celery_app.py` (broker URL, result backend, `task_serializer="json"`). Retry policy (`autoretry_for`) świadomie pominięta — brak dziś niestabilnej zależności zewnętrznej, którą warto by łapać (patrz `research/celery-research.md` sekcja 5).
- [x] Nowy serwis `worker` w `docker-compose.yml` (ten sam `Dockerfile`, `command: celery -A app.celery_app worker --loglevel=info`).

### 8. Limity czasowe dla zadań OCR

- [x] `task_time_limit` / `task_soft_time_limit`, żeby zawieszony OCR nie blokował workera w nieskończoność (`soft_time_limit=60`, `time_limit=90` na `process_cv_task`).

## Kolejność realizacji

1. **Punkty 1–2** (status w DB + endpointy) — samodzielna wartość, można wdrożyć dziś, bez Celery.
2. **Punkty 3, 7, 5, 4, 6, 8** — razem, jako jedna migracja na Celery, po domknięciu 1–2.

---

Odznaczaj `[x]` w miarę realizacji.
