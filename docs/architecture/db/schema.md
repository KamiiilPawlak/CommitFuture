# Baza danych

Dokument opisuje faktyczny stan schematu bazy danych i sposób łączenia się z nią — na podstawie kodu w `backend/app/models/`, `backend/app/db/database.py` i `backend/app/core/config.py`.

## Silnik i konfiguracja połączenia

- ORM: **SQLModel** (SQLAlchemy + Pydantic). Jeden globalny `engine` tworzony w `app/db/database.py:12` przez `create_engine(settings.DATABASE_URL, echo=True)`.
- `DATABASE_URL` pochodzi z `Settings` (`app/core/config.py`), wczytywane z pliku `.env` (`pydantic-settings`, `env_file=".env"`), np.:
  `postgresql+psycopg2://postgres:abcd1234@localhost:5432/commit_future`
- Driver: `psycopg2` (synchroniczny). `asyncpg` jest w zależnościach projektu, ale nie jest dziś używany — cały dostęp do bazy w aplikacji jest synchroniczny (`sqlmodel.Session`), nawet gdy wywołujący kod jest `async` (patrz np. `CVProcessingService._store`, który otwiera zwykłą synchroniczną `Session` wewnątrz).
- `init_db()` (`app/db/database.py:15-19`) woła `SQLModel.metadata.create_all(engine)` — to historyczny sposób tworzenia schematu, **zastępowany teraz Alembicem** (patrz [`migrations.md`](./migrations.md)). Funkcja wciąż istnieje w kodzie, ale nowe zmiany schematu powinny iść przez migracje, nie przez nią.
- `get_session()` (`app/db/database.py:22-24`) — generator sesji używany jako FastAPI `Depends` w routerach.

## Środowiska i nazwy baz

| Środowisko | Baza | Źródło konfiguracji |
| --- | --- | --- |
| Lokalny dev (bez Dockera) | `commit_future` | `backend/.env` |
| Testy jednostkowe/integracyjne (pytest) | efemeryczny kontener Postgres (`testcontainers`), nazwa `commit_future_test` | `backend/tests/conftest.py` — **nadpisuje** `DATABASE_URL` zmienną środowiskową przed importem `settings`, więc `.env.test` nie jest faktycznie używane przez `pytest` |
| Plik `.env.test` (obecnie nieużywany przez testy) | `commit_future_test` | `backend/.env.test` |
| Docker Compose (`api`/`worker`/`beat`) | `commit_future` | `docker-compose.yml`, serwis `postgres` (`POSTGRES_DB`) + zmienne `DATABASE_URL` w serwisach `api`/`worker`/`beat` |

> Uwaga: `tests/conftest.py` sam odpala kontener Postgres przez `testcontainers` i ustawia `DATABASE_URL` w `os.environ` **przed** importem `app.core.config`, więc wartość z `.env.test` nigdy nie jest realnie odczytywana w trakcie `pytest`. Plik `.env.test` zostaje jako dokumentacja intencji / ewentualny fallback, ale nie steruje dziś testami.

## Schemat — tabele

### `cv_document_lake` (model `CVDocumentLake`, `app/models/cv_document.py`)

Metadane fizycznego pliku CV w Data Lake — jeden wiersz per upload.

| Kolumna | Typ | Uwagi |
| --- | --- | --- |
| `id` | `UUID` (PK) | `default_factory=uuid4` |
| `original_filename` | `str` | nazwa pliku podana przez klienta (niezaufana, tylko metadana) |
| `storage_path` | `str` | ścieżka fizyczna na dysku (`storage/cv_uploads/<miesiąc>/<uuid>.pdf`) |
| `file_size_bytes` | `int` | |
| `mime_type` | `str` | domyślnie `application/pdf` |
| `created_at` | `datetime` | `default_factory=now(UTC)` |

### `cv_raw_text` (model `CVRawText`, `app/models/cv_raw_text.py`)

Surowy tekst po OCR/ekstrakcji — relacja 1:1 z `cv_document_lake`.

| Kolumna | Typ | Uwagi |
| --- | --- | --- |
| `cv_document_id` | `UUID` (PK, FK → `cv_document_lake.id`) | |
| `raw_text` | `str` | |
| `character_count` | `int` | |
| `word_count` | `int` | |
| `page_count` | `int \| None` | dziś zawsze `0`/`None` — liczenie stron nie jest wdrożone |
| `extraction_tool` | `str` | domyślnie `"pdfplumber"` |
| `metadata_json` | `JSONB \| None` | |
| `extracted_at` | `datetime` | |

### `cv_structured_data` (model `CVStructuredData`, `app/models/cv_structured_data.py`)

Wynik Etapu B (heurystyki) dla danego dokumentu CV — relacja 1:1 z `cv_document_lake`.

| Kolumna | Typ | Uwagi |
| --- | --- | --- |
| `cv_document_id` | `UUID` (PK, FK → `cv_document_lake.id`) | |
| `structured_data` | `JSONB \| None` | `None` przy `status="pending"` |
| `status` | `str` | `pending \| completed \| partial \| failed`, domyślnie `pending` |
| `processed_at` | `datetime` | |
| `recovery_attempts` | `int` | domyślnie `0`; liczba ponowień przez mechanizm odzyskiwania zawieszonych zadań (`app/services/cv_pipeline/recovery.py`) — dodane migracją `1691a8e1f341_initial_schema` |

### `job_posting` (model `JobPosting`, `app/models/job_posting.py`)

Ogłoszenie o pracę przyjęte do przetworzenia — jedna tabela (bez rozbicia na raw/structured jak w CV).

| Kolumna | Typ | Uwagi |
| --- | --- | --- |
| `id` | `UUID` (PK) | |
| `raw_text` | `str` | tekst ogłoszenia podany w żądaniu (`POST /job-postings`) |
| `structured_data` | `JSONB \| None` | wynik parsera (`app/services/job_pipline/transform/parse_job_posting.py`) |
| `status` | `str` | `pending \| completed \| failed`, domyślnie `pending` |
| `created_at` | `datetime` | |
| `processed_at` | `datetime \| None` | |

## Relacje

```
cv_document_lake (1) ──── (1) cv_raw_text        [FK: cv_raw_text.cv_document_id]
cv_document_lake (1) ──── (1) cv_structured_data [FK: cv_structured_data.cv_document_id]

job_posting — samodzielna tabela, brak FK do innych tabel
```

## Repozytoria (warstwa dostępu)

- `app/repositories/cv_repository.py` (`CVRepository`) — `create_lake_record`, `create_raw_text_record`, `upsert_structured_record` (insert-or-update po PK `cv_document_id`), `get_structured_by_lake_id`, `get_stale_pending`, `increment_recovery_attempts`, `count_structured_by_status`.
- `app/repositories/job_posting_repository.py` (`JobPostingRepository`) — `create`, `get_by_id`, `update_structured_data`.

Obie klasy przyjmują `sqlmodel.Session` w konstruktorze i udostępniają `commit()`/`rollback()` — sesja żyje albo w zakresie żądania HTTP (FastAPI `Depends(get_session)`), albo jest otwierana osobno wewnątrz zadania Celery (patrz [`dataflow.md`](./dataflow.md)).
