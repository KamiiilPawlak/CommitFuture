# Roadmapa — wdrożenie Celery

> Stan na: 2026-10-13. Ten dokument rozpisuje **kolejność i zakres PR-ów** potrzebnych do przejścia z `BackgroundTasks` na Celery. Zakłada się, że [`celery-migration-checklist.md`](./celery-migration-checklist.md) (lista punktów do zrobienia) i [`research/celery-research.md`](../../research/celery-research.md) (wyjaśnienie pojęć i architektury) są już przeczytane — tu jest tylko **plan działania**, bez teorii.
>
> Powiązane: [`roadmap.md`](./roadmap.md) Faza 4 (decyzja "czy w ogóle"), [`checklist.md`](../../checklist.md) P5, [`research/celery-redis-alembic-research.md`](../../research/celery-redis-alembic-research.md) (jak Celery/Redis/Alembic łączą się w jednym repo).
>
> **Tryb realizacji:** każda faza to jeden PR/commit, zatwierdzany przez właściciela repo między fazami — po skończeniu fazy czekamy na commit, dopiero potem ruszamy dalej. **Faza 5 (produkcja) jest obecnie wstrzymana** — wymaga Alembica i CI/CD, które jeszcze nie są wprowadzone w tym repo; wraca do gry, gdy [`ci-cd-roadmap.md`](./ci-cd-roadmap.md) (Fazy 1–7) i Alembic (`research/alembic-research.md`) zostaną wdrożone.

## 0. Warunek wejścia (czy już czas)

Zanim zacznie się Fazę 1 — sprawdzić sygnały z `celery-migration-checklist.md` ("Kiedy w ogóle przechodzić"). Jeśli żaden nie boli, ta roadmapa czeka — Redis/broker to nowy koszt operacyjny (YAGNI).

## 1. Stan wejściowy (co już jest zrobione, niezależnie od Celery)

- [x] Status przetwarzania (`pending/completed/partial/failed`) w `cv_structured_data` — już istnieje.
- [x] `GET /api/v1/cv/{cv_document_id}/structured` — Result API już działa (P5 w `checklist.md`), czyli klient ma skąd odebrać wynik niezależnie od tego, czy zadanie wykonuje `BackgroundTasks` czy Celery.
- [ ] Test integracyjny end-to-end (upload → poczekaj → `GET /structured`) — wciąż otwarty punkt z `checklist.md` P5, **zrobić przed Fazą 2**, bo to jedyny test, który wykryje regresję przy podmianie `BackgroundTasks` → `.delay()`.

To oznacza: checklist punkty 1–2 (status w DB + endpointy) są już zrealizowane. Ta roadmapa zaczyna się od punktu 3 checklisty ("fundamenty przed Celery" → "migracja").

## 2. Fazy (każda = jeden PR)

### Faza 1 — Infrastruktura brokera (bez dotykania kodu pipeline'u) ✅ wdrożone, czeka na commit

Cel: Redis działa lokalnie i w CI, ale `BackgroundTasks` wciąż robi całą pracę — zero ryzyka dla istniejącego pipeline'u.

- [x] Dodać serwis `redis` (`redis:7-alpine`) do `docker-compose.yml` z `healthcheck`.
- [x] Dodać `celery` + `redis` (klient Pythona) do `backend/pyproject.toml`.
- [x] Zmienne env: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (domyślne w `app/core/config.py`, nadpisane w `docker-compose.yml` na hostname `redis`; w repo nie ma `.env.example`, więc domyślne wartości `redis://localhost:6379/0` wystarczają bez edycji `.env`).
- [x] `app/celery_app.py` — instancja `Celery`, `task_serializer="json"`, **bez żadnych tasków jeszcze**.
- [ ] Smoke test: worker (`celery -A app.celery_app worker`) startuje lokalnie i w kontenerze, łączy się z Redisem — nic więcej.

### Faza 2 — Przeniesienie `process_and_store` do taska Celery

Cel: ten sam kod co dziś, tylko wołany przez `.delay()` zamiast `BackgroundTasks.add_task()`.

- [ ] `app/services/cv_pipeline/tasks.py` — `@celery_app.task def process_cv_task(cv_document_id): ...`, wołający dokładnie to, co dziś robi `CVProcessingService.process_and_store` (tylko przyjmujący `id`, nie obiekt ORM — patrz checklist punkt 4).
- [ ] Sesja DB otwierana/zamykana **wewnątrz** taska, nie wstrzykiwana przez FastAPI DI (checklist punkt 5).
- [ ] `ingestion.py`: `BackgroundTasks.add_task(...)` → `process_cv_task.delay(cv_document_id)`.
- [ ] Nowy serwis `worker` w `docker-compose.yml` (ten sam obraz `backend/Dockerfile`, `command: celery -A app.celery_app worker --loglevel=info`).
- [ ] `task_always_eager=True` w konfiguracji testowej — testy integracyjne (w tym ten z Fazy 0) **nie zmieniają się**, task wykonuje się synchronicznie jak dziś.
- [ ] Zweryfikować test end-to-end z sekcji 1 — musi przejść bez zmian w assercjach, tylko przez `task_always_eager`.

### Faza 3 — Odporność (to, czego `BackgroundTasks` nie dawał) ✅ wdrożone, czeka na commit

Cel: realny powód migracji — przetrwanie restartu, brak zawieszeń.

- [x] `acks_late=True` na `process_cv_task` + weryfikacja idempotencji (`upsert_structured_record` nadpisuje po PK `cv_document_id` — potwierdzone, checklist punkt 6 zamknięty).
- [x] `task_soft_time_limit=60` / `task_time_limit=90` na `process_cv_task` — zawieszony OCR/heurystyka nie blokuje workera w nieskończoność.
- [x] `broker_transport_options = {"visibility_timeout": 120}` w `app/celery_app.py` — **odkryte podczas testu**: domyślny `visibility_timeout` transportu Redis to 1h, więc bez tej zmiany `acks_late` działałby, ale zawieszone zadanie czekałoby na redelivery do godziny, nie do ~2 minut.
- [x] Manualny test wykonany realnie na `docker compose` (`redis` + `worker`): wysłano zadanie testowe, `docker kill -s SIGKILL` na workerze w trakcie wykonania, nowy worker przejął zadanie i je zakończył (`received` → `succeeded`) po upłynięciu `visibility_timeout` — zadanie **nie przepadło**. Kod testowy był tymczasowy, usunięty z repo po weryfikacji.

### Faza 4 — Obserwowalność i porządki ✅ wdrożone, czeka na commit

Cel: wiadomo, co się dzieje z zadaniami bez grepowania logów.

- [x] `GET /api/v1/cv/stats` — zlicza dokumenty w `cv_structured_data` per status (`pending/completed/partial/failed`) na podstawie `CVRepository.count_structured_by_status()`. Flower uznany za niepotrzebny na tym etapie (prosty `GROUP BY status` wystarcza, zero dodatkowej usługi do utrzymania).
- [x] Usunięto `BackgroundTasks` z `ingestion.py` całkowicie (import i nieużywany parametr) — martwy kod po Fazie 2.
- [x] Zaktualizowano `roadmap.md` Faza 4 (decyzja "Celery vs BackgroundTasks" odznaczona jako rozstrzygnięta na Celery) i `checklist.md` P5 (dopisane, że trwała kolejka jest już wdrożona) oraz `celery-migration-checklist.md` (odznaczone wszystkie zrealizowane punkty fundamentów).

### Faza 5 — Produkcja (WSTRZYMANA — nie realizować) — wymaga Alembica i CI/CD, których jeszcze nie ma w tym repo

Cel: to samo co lokalnie, ale hostowane.

- [ ] Wybór hostingu Redisa (Upstash / Render Key Value — patrz `research/redis-research.md` sekcja 6, do zweryfikowania w `cd-research.md`, jeśli temat stanie się realny).
- [ ] Worker jako osobny proces/serwis na platformie deploymentu (np. "Background Worker" na Render), skalowany niezależnie od `api`.
- [ ] Alembic + Celery razem w CI/CD — patrz `research/celery-redis-alembic-research.md` dla pełnego obrazu (migracje muszą się wykonać przed startem workera, nie równolegle z nim).

## 3. Co NIE jest w tej roadmapie (świadomie odłożone)

- **Celery Beat** (zadania okresowe, np. odzyskiwanie zawieszonych `pending`) — osobna decyzja, dziś nic tego nie wymaga poza `roadmap.md` Faza 4 ("odzyskiwanie zawieszonych"). Dodać jako Faza 6, jeśli/kiedy stanie się potrzebne.
- **Wiele kolejek** (`queue="ocr"` vs domyślna) — niepotrzebne przy jednym typie długiej operacji (OCR); dodać, jeśli pojawi się drugi typ zadania o innym profilu czasowym.
- **Retry z backoffem na zewnętrznych zależnościach** — w repo nie ma dziś niestabilnej zależności zewnętrznej (brak LLM/Ollama), więc `autoretry_for` nie ma dziś czego łapać — patrz `celery-research.md` sekcja 5.

## 4. Kryterium "zrobione"

Migracja jest kompletna, gdy: restart kontenera `worker` w trakcie przetwarzania CV **nie gubi** zadania (task wraca do kolejki albo jest podjęty przez inny worker), a testy integracyjne przechodzą bez realnego Redisa (`task_always_eager=True`).
