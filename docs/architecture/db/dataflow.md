# Przepływ danych (stan aktualny — Celery)

Dokument opisuje aktualny, rzeczywisty przepływ danych dla dwóch niezależnych pipeline'ów: **CV** i **ogłoszenie o pracę**. Oba działają na tym samym wzorcu: szybki zapis synchroniczny w ramach żądania HTTP + ciężkie przetwarzanie zlecone do Celery.

> Starszy dokument w katalogu głównym repo (`dataflow.md`) opisuje wcześniejszą wersję architektury, oparta na FastAPI `BackgroundTasks` — od migracji opisanej w `celery-roadmap.md` jest nieaktualny. Ten dokument jest jego następcą dla ścieżki CV i rozszerza opis o ścieżkę ogłoszeń o pracę. Szczegóły samej logiki heurystycznej Etapu B (czyszczenie/normalizacja/ekstrakcja) opisuje `cv-etl-pipline.md` — ten dokument skupia się na przepływie między komponentami (HTTP → DB → Celery → DB), nie powtarza algorytmów ekstrakcji.

**Mechanizm asynchroniczności:** Celery + Redis (broker i result backend), nie `BackgroundTasks`. Konfiguracja: `app/celery_app.py`.

---

## Ścieżka CV: `POST /cv/upload` → `GET /cv/{id}/structured`

```
1. Klient → POST /cv/upload (multipart, plik PDF)
   app/api/v1/routes/ingestion.py: upload_cv_document
       │
       ▼
2. IngestionService.process_cv_document(file)   [SYNCHRONICZNIE, w ramach żądania]
       a. StorageService.save_pdf_file            → plik na dysku (storage/cv_uploads/<miesiąc>/<uuid>.pdf)
       b. CVRepository.create_lake_record         → wiersz cv_document_lake
       c. OCRService.process_document             → pdfplumber / fallback pytesseract
       d. CVRepository.create_raw_text_record     → wiersz cv_raw_text, commit
       │
       ▼
3. Router wstawia pending wiersz:
   ingestion_service.repository.upsert_structured_record(status="pending") + commit()
       │
       ▼
4. Router zleca zadanie Celery:
   process_cv_task.delay(str(lake_record.id), raw_text_record.raw_text)
       │
       ▼
5. Odpowiedź HTTP 201 (CVIngestionResponse) — zawiera już surowy tekst, ale NIE wynik heurystyk
       │
       │  (Celery worker, osobny proces — app/services/cv_pipeline/tasks.py: process_cv_task)
       ▼
6. CVProcessingService.process_and_store(cv_document_id, raw_text)
       a. CVPipelineOrchestrator.process_cv(raw_text)   → clean_ocr_text → normalize_text → extract_all
          (szczegóły: cv-etl-pipline.md, kroki 6-8; dziś czysto heurystyczne, bez LLM)
       b. build_unified_record(...)                     → finalny CVStructuredRecord
       c. Nowa sesja DB (Session(engine), niezależna od request scope)
          CVRepository.upsert_structured_record(status="completed"/"failed") → UPDATE po PK, commit
       │
       ▼
7. Klient pollinguje GET /cv/{cv_document_id}/structured
   — przy status="pending" nadal zwraca 200 z structured_data=null (frontend sam odróżnia pending od gotowego wyniku)
```

**Idempotencja i odzyskiwanie:** `upsert_structured_record` nadpisuje po PK `cv_document_id`, więc ponowne zlecenie zadania dla tego samego dokumentu nie tworzy duplikatu. Zadania mają `acks_late=True`, `soft_time_limit=60`, `time_limit=90` (`app/services/cv_pipeline/tasks.py`) — crash workera w trakcie przetwarzania nie gubi zadania (broker redostarcza), ale długo wisząca OCR-owa operacja zostanie ubita po przekroczeniu limitu czasu.

### Odzyskiwanie zawieszonych dokumentów (Celery Beat)

`app/services/cv_pipeline/recovery.py` + harmonogram w `celery_app.py` (`beat_schedule["recover-stale-pending-cv"]`, interwał `STALE_PENDING_CHECK_INTERVAL_SECONDS`):

```
Celery Beat (co STALE_PENDING_CHECK_INTERVAL_SECONDS)
   → recover_stale_pending_task
   → recover_stale_pending_cv_documents()
       dla każdego cv_structured_data.status="pending" starszego niż STALE_PENDING_THRESHOLD_MINUTES:
         - recovery_attempts >= STALE_PENDING_MAX_ATTEMPTS → status="failed" (poddane)
         - brak cv_raw_text dla dokumentu                  → status="failed" (nie da się ponowić)
         - inaczej → increment_recovery_attempts(), process_cv_task.delay(...) ponownie
```

To rekompensuje scenariusz, w którym zadanie Celery zginęło bez śladu (np. worker zabity w trakcie przetwarzania, zanim zdążył zaktualizować status) — bez tego dokument zostałby w `pending` na zawsze.

---

## Ścieżka ogłoszenia o pracę: `POST /job-postings` → `GET /job-postings/{id}`

Prostszy wariant tego samego wzorca — bez etapu OCR/Data Lake, tekst przychodzi od razu jako JSON.

```
1. Klient → POST /job-postings  {"raw_text": "..."}
   app/api/v1/routes/job_posting.py: submit_job_posting
       │
       ▼
2. JobPostingRepository.create(payload.raw_text)   → wiersz job_posting (status="pending"), commit
       │
       ▼
3. process_job_posting_task.delay(str(job_posting.id), job_posting.raw_text)
       │
       ▼
4. Odpowiedź HTTP 201 (JobPostingSubmitResponse: job_posting_id, status="pending")
       │
       │ (Celery worker — app/services/job_pipline/tasks.py: process_job_posting_task)
       ▼
5. JobPostingProcessingService.process_and_store(job_posting_id, raw_text)
       a. parse_job_posting(raw_text)   (app/services/job_pipline/transform/parse_job_posting.py)
       b. Nowa sesja DB → JobPostingRepository.update_structured_data(status="completed"/"failed"), commit
       │
       ▼
6. Klient → GET /job-postings/{job_posting_id} → {status, structured_data, processed_at}
```

**Różnice względem ścieżki CV:**
- Brak Data Lake / brak osobnej tabeli na surowy tekst — `raw_text` i `structured_data` żyją w jednej tabeli `job_posting`.
- Status ma tylko `pending | completed | failed` (brak `partial`).
- Brak mechanizmu odzyskiwania zawieszonych zadań (`recovery.py` istnieje tylko dla ścieżki CV) — zawieszone ogłoszenie w `pending` nie jest dziś automatycznie ponawiane.

---

## Konfiguracja Celery (wspólna dla obu ścieżek)

**Plik:** `app/celery_app.py`

| Ustawienie | Wartość | Uwagi |
| --- | --- | --- |
| `broker` / `backend` | `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` (`redis://...`) | ten sam Redis dla brokera i wyników |
| `task_serializer` / `result_serializer` / `accept_content` | `json` | zadania przyjmują tylko dane serializowalne (`str`, nie obiekty ORM) |
| `broker_transport_options.visibility_timeout` | 120s | jak długo broker czeka, zanim uzna zadanie za niedostarczone i odda je ponownie |
| `imports` | `cv_pipeline.tasks`, `job_pipline.tasks` | rejestracja tasków przy starcie workera |
| `beat_schedule` | `recover-stale-pending-cv` | jedyne zadanie okresowe dziś skonfigurowane |

**Procesy w Docker Compose** (`docker-compose.yml`): `api` (FastAPI/uvicorn), `worker` (`celery ... worker`), `beat` (`celery ... beat`) — trzy niezależne kontenery współdzielące ten sam obraz i bazę `commit_future`.

## Co jest poza zakresem tego dokumentu

- Dalsze etapy po zapisaniu `cv_structured_data`/`job_posting` (matching CV ↔ ogłoszenie) — `app/services/matching_engine/` istnieje jako kod, ale nie jest tu opisany; patrz `matching-scoring.md`.
- Szczegóły samej ekstrakcji heurystycznej CV (regexy, słowniki, segmentacja) — `cv-etl-pipline.md`.
- Migracje schematu bazy używanej przez te tabele — [`migrations.md`](./migrations.md), model danych — [`database.md`](./database.md).
