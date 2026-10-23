# Roadmapa — pełny ETL po stronie CV

> Stan na: 2026-10-05, branch `docs/update-docs`. Ten dokument opisuje, co **faktycznie** jest zaimplementowane w `backend/app` (w tym zmiany jeszcze niezacommitowane w working tree), jakich elementów brakuje do uznania pipeline'u CV za "pełny ETL", i w jakiej kolejności je domykać.
>
> Powiązane dokumenty: [`cv-etl-pipline.md`](./cv-etl-pipline.md) (opis krok-po-kroku Etapu A/B — **nieaktualny, wciąż opisuje LLM/Ollama**, patrz niżej), [`checklist.md`](../../checklist.md) (zaktualizowany 2026-10-20, zawiera dzisiejszy, realny stan projektu), [`matching-engine-roadmap.md`](./matching-engine-roadmap.md) (silnik matchingu CV↔ogłoszenie, cosine similarity, bez LLM — zrealizowany w całości).
>
> **Korekta 2026-10-20:** cała ta roadmapa pochodzi z okresu, gdy Etap B był opisywany jako docelowo sparowany z LLM (Ollama). To nigdy nie zostało trwale wdrożone — dzisiejszy pipeline to wyłącznie OCR + heurystyka, a dopasowanie do ogłoszeń liczy osobny `matching_engine` przez cosine similarity. Fazy 1–2 niżej są już zrealizowane; aktualny stan patrz `checklist.md`.

## 0. Ważna korekta względem `cv-etl-pipline.md`

`cv-etl-pipline.md` i `checklist.md` opisują Etap B jako **niepodłączony do API**. To już nieaktualne — w working tree (niecommitowane zmiany w `ingestion.py`, `cv_repository.py`, `database.py`, `models/__init__.py` + nowy plik `cv_structured_data.py`) pipeline jest spięty end-to-end:

```
POST /cv/upload
  → IngestionService.process_cv_document   (Etap A: zapis + OCR, jak dotychczas)
  → BackgroundTasks.add_task(CVProcessingService.process_and_store)
       → CVPipelineOrchestrator.process_cv  (Etap B: cleaning → normalizacja → heurystyka)
       → CVRepository.upsert_structured_record → tabela cv_structured_data (status: pending|completed|partial|failed)
```

**Skutek:** punkty 1–3 z sekcji P0 w `checklist.md` są już zrealizowane (oba dokumenty wymagają aktualizacji — patrz [Faza 4](#faza-4--dokumentacja-i-porządki)). Ta roadmapa skupia się na tym, co zostaje **po** tym domknięciu.

## 1. Co działa dziś (po uwzględnieniu working tree)

- Upload → walidacja rozszerzenia → Data Lake → OCR (pdfplumber/Tesseract fallback) → `cv_raw_text`.
- Przetwarzanie w tle: cleaning → normalizacja → heurystyka (email/telefon/daty/tech/stanowiska/staż) → zapis do `cv_structured_data` jako JSONB. **Korekta:** nie ma żadnego kroku LLM/Ollama w pipeline — wcześniejsze wersje tego dokumentu opisywały fazę LLM jako plan, który nigdy nie został zaimplementowany; dzisiejszy Etap B to wyłącznie OCR + heurystyka.
- Status przetwarzania (`pending/completed/partial/failed`) jest zapisywany, ale **nic go dziś nie odczytuje** — patrz brak #1 poniżej.

## 2. Analiza braków

### Brak krytyczny: brak kontraktu wynikowego (Result API)

Przetwarzanie Etapu B dzieje się w `BackgroundTasks` — klient dostaje odpowiedź `201` zanim Etap B się zacznie, i **nie ma żadnego endpointu**, by:
- sprawdzić status (`pending/completed/partial/failed`),
- odebrać `structured_data` po zakończeniu,
- dowiedzieć się, że przetwarzanie się nie powiodło.

To jedyny brak, który czyni dzisiejszy pipeline praktycznie bezużytecznym z perspektywy frontendu/klienta API — dane trafiają do bazy, ale nie ma z nich żadnego "wyjścia".

### Bezpieczeństwo i walidacja uploadu (z `checklist.md`, wciąż aktualne)

- `verify_file_integrity()` (magic bytes, `python-magic`) — zdefiniowana w `app/core/security.py`, **nigdzie niewywoływana**.
- `settings.MAX_FILE_SIZE` (5 MB) — zdefiniowany, **niesprawdzany** w `StorageService.save_pdf_file`.
- Usunięty `docs/architecture/adr/0001-magic-bytes-validation.md` opisywał decyzję o magic bytes — decyzja i jej uzasadnienie zniknęły z repo wraz z plikiem.

### Jakość danych z pipeline'u

- **`page_count` zawsze `0`** w `cv_raw_text` — liczba stron PDF nie jest liczona nigdzie (ani w ścieżce `pdfplumber`, ani w OCR).
- **Zduplikowana/martwa logika domenowa:** `ExperienceService.calculate_experience` i `TechStackValidator` istnieją i są przetestowane jednostkowo, ale pipeline korzysta tylko z równoległej logiki w `experience_calc.py` i `FlashLookupEngine` — do decyzji: scalić czy usunąć.

### Odporność / obserwowalność przetwarzania w tle

- `BackgroundTasks` z FastAPI działa w procesie API — **restart serwera w trakcie przetwarzania gubi zadanie bez śladu** (status zostaje w `pending` na zawsze, nic tego nie wykrywa). Brak kolejki (Celery/RQ/Arq) i brak retry/DLQ na poziomie infrastruktury, nie tylko klienta Ollamy.
- Brak metryk/alertów na odsetek `failed`/`partial` — dziś widoczne tylko przez ręczne zapytanie SQL albo grep logów.

### Przenośność / infrastruktura

- `OCRConfig.TESSERACT_CMD` zahardkodowany na Windows (`C:\Program Files\Tesseract-OCR\tesseract.exe`) — pipeline nie odpali się w kontenerze Linux/CI bez zmiany kodu.

### Testy

Dzisiejsze testy pokrywają poszczególne komponenty (`cleaning`, `normalization`, `heuristic`) i cały `CVPipelineOrchestrator.process_cv` w izolacji. **Nie ma testu end-to-end przez API** (`POST /cv/upload` → poczekaj na `BackgroundTasks` → sprawdź `cv_structured_data` w bazie) — czyli brak pokrycia właśnie tego połączenia, które jest teraz sercem pipeline'u.

## 3. Proponowane fazy

### Faza 0 — Domknięcie podłączenia (już zrealizowane w working tree)

- [x] `CVPipelineOrchestrator.process_cv` wywoływany po zapisie `cv_raw_text` (przez `BackgroundTasks`).
- [x] Tabela `cv_structured_data` (model `CVStructuredData`) jako miejsce docelowe wyniku.
- [x] Zapis wyniku z `status` (`pending/completed/partial/failed`).
- [ ] Commit tych zmian + aktualizacja `cv-etl-pipline.md`/`checklist.md`, żeby nie rozjeżdżały się z kodem (patrz Faza 4).

### Faza 1 — Result API (odblokowuje realne użycie pipeline'u) ✅

Zrealizowane, choć inaczej niż pierwotnie zapisano niżej (status i wynik połączone w jeden endpoint, nie dwa osobne):

- [x] `GET /api/v1/cv/{cv_document_id}/structured` — zwraca `status` oraz `structured_data` z `cv_structured_data` (404, jeśli rekordu jeszcze nie ma); zastępuje planowany podział na `/status` + `/result`.
- [x] `GET /api/v1/cv/stats` — zliczenia per status (`pending/completed/partial/failed`), dodatkowo ponad to, co planowano w tej fazie.
- [x] `ProcessedCVTO` (`app/schema/ingestion_dto.py`) rozstrzygnięte.
- [x] Test integracyjny end-to-end: `backend/tests/integration/api/test_cv_pipeline_e2e.py` — upload → Celery (`task_always_eager`) → `GET /structured`/`GET /stats`.

### Faza 2 — Bezpieczeństwo i limity uploadu ✅

- [x] `verify_file_integrity()` podłączone do `StorageService.save_pdf_file` (magic bytes przed zapisem na dysk).
- [x] `settings.MAX_FILE_SIZE` wyegzekwowane w `StorageService`.
- [x] ADR o magic bytes istnieje (`docs/architecture/adr/0001-magic-bytes-validation.md`).

### Faza 3 — Jakość i odporność danych z Etapu B

- [x] `page_count` liczony realnie przy ekstrakcji, nie stały `0`.
- [ ] Decyzja: `ExperienceService`/`TechStackValidator` — podłączyć do pipeline'u (usuwając duplikację w `experience_calc.py`/`FlashLookupEngine`) albo usunąć jako martwy kod. **Wciąż otwarte.**

### Faza 4 — Odporność przetwarzania w tle i obserwowalność

- [x] Ocenić, czy `BackgroundTasks` wystarcza na produkcję, czy potrzebna jest trwała kolejka (Celery/Arq/RQ) z retry/DLQ niezależnym od życia procesu API — **decyzja: Celery + Redis**, wdrożone (patrz [`celery-roadmap.md`](./celery-roadmap.md) Fazy 1–4). `BackgroundTasks` usunięty z `ingestion.py`, `POST /cv/upload` woła `process_cv_task.delay(...)`; `acks_late=True` + `visibility_timeout=120` w `app/celery_app.py` rozwiązują problem zamrażania w `pending` przy restarcie.
- [x] Zadanie/endpoint do "odzyskania" zawieszonych w `pending` dłużej niż X minut (retry albo oznaczenie `failed`) — **zrobione: Celery Beat**, patrz [`celery-roadmap.md`](./celery-roadmap.md) Faza 6 i [`research/celery-research.md`](../../research/celery-research.md) sekcja 10.
- [x] Metryka/log agregujący odsetek `completed/partial/failed` do szybkiej oceny zdrowia pipeline'u — `GET /api/v1/cv/stats`.

### Faza 5 — Przenośność i dokumentacja

- [x] `OCRConfig.TESSERACT_CMD` → zmienna środowiskowa/config, pipeline odpala się w kontenerze/CI.
- [ ] Zaktualizować `cv-etl-pipline.md` — wciąż opisuje Etap B jako sparowany z LLM (Ollama) i niepodłączony do API; nieaktualne względem kodu (2026-10-20).
- [x] `checklist.md` zaktualizowany (2026-10-20) — zrealizowane punkty odznaczone, LLM/Ollama usunięte z opisu, dodany `matching_engine` i realne otwarte luki (frontend matchingu, CI bez testów, brak CD).
- [x] Zdecydować o losie usuniętych plików w `docs/architecture/` (diagramy `.drawio.svg`, `dependencies.svg`, `classes/packages_cv_matcher.png`, `security_policies.md`) — **zrobione: nie odtwarzamy, `overview.md` zastępuje je opisem tekstowym** (decyzja i uzasadnienie per plik w `overview.md`, sekcja "Historia tego dokumentu").

## 4. Decyzje otwarte dla właściciela produktu/repo

1. **Result API — sync czy async?** Czy `/cv/upload` powinien móc opcjonalnie czekać (parametr `?sync=true`) na wynik Etapu B dla małych plików, czy zawsze tylko fire-and-forget + polling przez `/status`?
2. ~~**Kolejka w tle** — czy zostajemy przy `BackgroundTasks` (prostsze, ale bez trwałości) do MVP, czy inwestujemy teraz w Celery/Arq (Faza 4) przed pierwszym wdrożeniem produkcyjnym?~~ **Rozstrzygnięte: Celery + Redis**, patrz [`celery-roadmap.md`](./celery-roadmap.md).

---

**Jak korzystać z tej roadmapy:** odznaczaj `[x]` w miarę realizacji. Każda faza nadaje się na odrębny PR — Faza 1 (Result API) powinna wejść przed czymkolwiek innym, bo bez niej pipeline Etapu B pozostaje praktycznie niewidoczny dla konsumentów API.
