# Architecture Overview — CommitFuture (CV AI Matcher)

> Stan na: 2026-10-05. Ten dokument jest punktem wejścia do dokumentacji architektury — opisuje całość systemu na wysokim poziomie. Szczegóły konkretnych obszarów są w osobnych dokumentach (patrz [Powiązane dokumenty](#powiązane-dokumenty)), żeby nie duplikować treści i nie rozjeżdżać się z kodem.

## Cel systemu

CommitFuture (nazwa produktu: **CV AI Matcher**) ma dopasowywać kandydatów do ofert pracy na podstawie treści CV, przetworzonej do ustrukturyzowanej formy przez lokalny pipeline OCR + LLM. W repozytorium faktycznie zaimplementowana jest dziś **wyłącznie strona CV** (upload → OCR → ETL/NLP → zapis ustrukturyzowanego wyniku). Strona "oferty pracy" (scraping + matching) ma na razie tylko szkielet modelu danych — patrz [Zakres: co istnieje vs. co jest planowane](#zakres-co-istnieje-vs-co-jest-planowane).

## Powiązane dokumenty

| Dokument | Zawartość |
| --- | --- |
| [`cv-etl-pipline.md`](./cv-etl-pipline.md) | Szczegółowy, krok-po-kroku opis pipeline'u CV (Etap A — Ingestion, Etap B — ETL/NLP) na podstawie faktycznego kodu, z tabelami konfiguracji i testów. |
| [`roadmap.md`](./roadmap.md) | Analiza braków względem "pełnego ETL" i proponowane fazy domykania (Result API, kolejka w tle, obserwowalność). |
| [`adr/0001-magic-bytes-validation.md`](./adr/0001-magic-bytes-validation.md) | Decyzja architektoniczna o walidacji plików przez magic bytes. |
| [`../../checklist.md`](../../checklist.md) | Lista TODO wg priorytetów (P0–P4), część punktów już zrealizowana. |

Ten dokument **nie opisuje** przebiegu pipeline'u krok po kroku — to robi `cv-etl-pipline.md`. Tutaj chodzi o to, jak komponenty systemu się do siebie składają i gdzie czego szukać w kodzie.

## Komponenty systemu (`docker-compose.yml`)

```text
┌──────────────┐      HTTP (multipart/form-data)
│   Klient     │ ───────────────────────────────┐
└──────────────┘                                 ▼
                                        ┌───────────────────┐
                                        │  api (FastAPI)     │  :8000
                                        │  backend/app       │
                                        └─────────┬──────────┘
                                                   │
                      ┌────────────────────────────┼─────────────────────────┐
                      ▼                             ▼                         ▼
             ┌─────────────────┐           ┌─────────────────┐      ┌─────────────────┐
             │ postgres         │           │ ollama           │      │ storage/         │
             │ (cv_ai_matcher)  │  :5432    │ (qwen2.5:3b)     │ :11434│ cv_uploads/     │
             └─────────────────┘           └─────────────────┘      │ (dysk lokalny)   │
                                                                      └─────────────────┘

             ┌─────────────────┐
             │ mkdocs           │  :8001  — serwuje statyczną dokumentację z `docs/`
             └─────────────────┘
```

- **api** — jedyny serwis z logiką biznesową; FastAPI + SQLModel, uruchamiany z `backend/Dockerfile`, montuje kod na żywo (`--reload`) w dev.
- **postgres** — jedna baza `cv_ai_matcher`, bez rozdzielenia na schematy; healthcheck blokuje start `api`, aż baza odpowiada.
- **ollama** — lokalny serwer LLM; kontener przy starcie sam pobiera model `qwen2.5:3b` (`ollama pull`), więc pierwszy start trwa dłużej.
- **mkdocs** — serwuje ten katalog (`docs/`) jako stronę dokumentacji, niezależnie od `api`.
- **storage/cv_uploads/** — pliki PDF trzymane na dysku kontenera/hosta (bind mount `./backend:/code`), nie w obiekcie blob/S3 — patrz uwaga o przenośności w `roadmap.md` (Faza 5).

## Mapa modułów (`backend/app`)

| Katalog | Rola |
| --- | --- |
| `api/v1/routes/` | Warstwa HTTP — routery FastAPI (`ingestion.py`, `health.py`). Tylko mapowanie żądań/wyjątków, bez logiki domenowej. |
| `core/` | Konfiguracja (`config.py` — `Settings` z `.env`, `OCRConfig`), bezpieczeństwo plików (`security.py`), logowanie (`logger.py`). |
| `db/` | `database.py` — silnik SQLAlchemy/SQLModel, `init_db()`, `get_session()` (DI dla FastAPI). |
| `models/` | Tabele SQLModel: `CVDocumentLake`, `CVRawText`, `CVStructuredData` (aktywnie używane), `DataLakeScrapper` (zdefiniowana, niepodłączona do żadnego serwisu). |
| `repositories/` | `CVRepository` — jedyny punkt dostępu do tabel CV (lake/raw_text/structured), hermetyzuje `Session`. |
| `schema/` | Pydantic DTO: `ingestion_dto.py` (odpowiedzi API), `cv_llm.py` (kontrakt JSON Schema wymuszany na Ollamie), `scraper_dto.py` (dla nieużywanego jeszcze modelu scrapera). |
| `services/ingestion_service/` | Etap A: `IngestionService` (orkiestracja), `StorageService` (zapis/odczyt plików + walidacja), `OCRService` (pdfplumber/Tesseract), `storage_path_provider.py`. |
| `services/etl_cv_service/` | Etap B: `pipeline.py` (`CVPipelineOrchestrator`), `cleaning.py`, `normalization.py`, `heuristic/` (ekstrakcja regułowa), `llm/` (klient Ollama), `validation.py` (walidacja krzyżowa LLM↔heurystyka), `dictionaries/` (słownik tech stacku + `TechStackValidator`), `processing_service.py` (`CVProcessingService` — łączy Etap A i B, wołany z `BackgroundTasks`). |

## Przepływ danych (skrót — szczegóły w `cv-etl-pipline.md`)

```text
POST /api/v1/cv/upload
  → IngestionService.process_cv_document   (Etap A: walidacja, zapis do Data Lake, OCR, zapis cv_raw_text)
  → odpowiedź 201 z surowym tekstem
  → BackgroundTasks: CVProcessingService.process_and_store
       → CVPipelineOrchestrator.process_cv  (Etap B: cleaning → normalizacja → heurystyka → LLM → walidacja krzyżowa)
       → CVRepository.upsert_structured_record → tabela cv_structured_data (status: pending|completed|partial|failed)
```

Klient dostaje odpowiedź HTTP zanim Etap B się zakończy (przetwarzanie w tle) — dziś **nie ma endpointu**, by odebrać wynik Etapu B po fakcie; to największy udokumentowany brak, patrz `roadmap.md`, sekcja "Result API".

## Zakres: co istnieje vs. co jest planowane

| Obszar | Status |
| --- | --- |
| Upload CV + OCR (Etap A) | ✅ Zaimplementowane i podłączone do API. |
| ETL/NLP CV (Etap B: heurystyka + LLM) | ✅ Zaimplementowane i podłączone (przez `BackgroundTasks`), wynik trafia do `cv_structured_data`. |
| Walidacja bezpieczeństwa uploadu (magic bytes, limit rozmiaru) | ✅ Zaimplementowane (`StorageService.save_pdf_file`). |
| Walidacja krzyżowa LLM ↔ heurystyka (detekcja halucynacji) | ✅ Zaimplementowane (`validation.py`), wynik jako ostrzeżenia, nie hard-fail. |
| Odbiór wyniku Etapu B przez API (Result API) | ❌ Brak — `cv_structured_data` jest zapisywane, ale nieodczytywane przez żaden endpoint. |
| Scraping ofert pracy | ⚠️ Tylko model danych (`DataLakeScrapper`) i DTO — brak serwisu, brak podłączenia do API. |
| Matching CV ↔ oferta pracy | ❌ Brak — nie istnieje jeszcze żaden kod realizujący samo dopasowanie; jest to cel końcowy produktu, nie zaimplementowany etap. |
| Trwała kolejka zadań w tle (zamiast `BackgroundTasks`) | ❌ Brak — patrz `roadmap.md`, Faza 4 (ryzyko utraty zadania przy restarcie API). |

## Historia tego dokumentu

Wcześniejsza wersja dokumentacji architektury opierała się na diagramach graficznych (`classes_cv_matcher.png`, `packages_cv_matcher.png`, `dependencies.svg`, pliki `.drawio.svg` w `diagrams/`) oraz odrębnym `security_policies.md`. Te pliki zostały usunięte na branchu `docs/update-docs`, bo opisywały kroki pipeline'u ("Document Detection", "Quality Check", "Section Detection"), które nie istnieją jako osobne moduły w kodzie. Ten dokument razem z `cv-etl-pipline.md` zastępuje je opisem tekstowym, aktualizowanym wraz z kodem; `security_policies.md` zasługuje na odtworzenie jako osobny dokument, jeśli opisane w nim zasady są nadal aktualne — patrz `checklist.md`, sekcja P4.
