# Roadmapa — pełny ETL po stronie CV

> Stan na: 2026-10-05, branch `docs/update-docs`. Ten dokument opisuje, co **faktycznie** jest zaimplementowane w `backend/app` (w tym zmiany jeszcze niezacommitowane w working tree), jakich elementów brakuje do uznania pipeline'u CV za "pełny ETL", i w jakiej kolejności je domykać.
>
> Powiązane dokumenty: [`cv-etl-pipline.md`](./cv-etl-pipline.md) (opis krok-po-kroku Etapu A/B — **częściowo nieaktualny**, patrz niżej), [`checklist.md`](../../checklist.md) (wcześniejsza lista TODO, częściowo już zrealizowana).

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

### Faza 1 — Result API (odblokowuje realne użycie pipeline'u)

Priorytet najwyższy: bez tego Etap B produkuje dane, których nikt nie może odebrać.

- [ ] `GET /api/v1/cv/{cv_document_id}/status` — zwraca `status` z `cv_structured_data` (albo `pending`, jeśli rekordu jeszcze nie ma).
- [ ] `GET /api/v1/cv/{cv_document_id}/result` — zwraca `structured_data` gdy `status in {completed, partial}`; 404/409 gdy `pending`/`failed`.
- [ ] Rozstrzygnąć `ProcessedCVTO` (`app/schema/ingestion_dto.py`) — zdefiniowane, nieużywane; albo staje się DTO odpowiedzi `/result`, albo zostaje usunięte.
- [ ] Test integracyjny end-to-end: upload → poczekaj na background task → `GET /result` zwraca dane zgodne z tym, co zapisał `CVProcessingService`.

### Faza 2 — Bezpieczeństwo i limity uploadu

- [ ] Podłącz `verify_file_integrity()` do `StorageService.save_pdf_file` (magic bytes przed zapisem na dysk).
- [ ] Wyegzekwuj `settings.MAX_FILE_SIZE` w `StorageService` (odrzuć plik > 5 MB z czytelnym błędem 400, nie 500 po zapełnieniu dysku).
- [ ] Nowy ADR opisujący decyzję o magic bytes (zastępujący usunięty `0001-magic-bytes-validation.md`), skoro mechanizm faktycznie wchodzi do użycia.

### Faza 3 — Jakość i odporność danych z Etapu B

- [ ] Policz `page_count` przy ekstrakcji (`pdfplumber`/`pdf2image`) i zapisz do `cv_raw_text` zamiast stałego `0`.
- [ ] Decyzja: `ExperienceService`/`TechStackValidator` — podłączyć do pipeline'u (usuwając duplikację w `experience_calc.py`/`FlashLookupEngine`) albo usunąć jako martwy kod.

### Faza 4 — Odporność przetwarzania w tle i obserwowalność

- [x] Ocenić, czy `BackgroundTasks` wystarcza na produkcję, czy potrzebna jest trwała kolejka (Celery/Arq/RQ) z retry/DLQ niezależnym od życia procesu API — **decyzja: Celery + Redis**, wdrożone (patrz [`celery-roadmap.md`](./celery-roadmap.md) Fazy 1–4). `BackgroundTasks` usunięty z `ingestion.py`, `POST /cv/upload` woła `process_cv_task.delay(...)`; `acks_late=True` + `visibility_timeout=120` w `app/celery_app.py` rozwiązują problem zamrażania w `pending` przy restarcie.
- [ ] Zadanie/endpoint do "odzyskania" zawieszonych w `pending` dłużej niż X minut (retry albo oznaczenie `failed`) — osobna decyzja, wymaga Celery Beat; świadomie odłożone (patrz `celery-roadmap.md` sekcja 3).
- [x] Metryka/log agregujący odsetek `completed/partial/failed` do szybkiej oceny zdrowia pipeline'u — `GET /api/v1/cv/stats`.

### Faza 5 — Przenośność i dokumentacja

- [ ] `OCRConfig.TESSERACT_CMD` → zmienna środowiskowa/config, żeby pipeline odpalał się w kontenerze/CI.
- [ ] Zaktualizować `cv-etl-pipline.md`, żeby odzwierciedlał Fazę 0 jako zrealizowaną (dziś opisuje Etap B jako niepodłączony).
- [ ] Zaktualizować `checklist.md` (odznaczyć zrealizowane punkty P0, przeniosić pozostałe do odpowiednich faz tej roadmapy, żeby nie istniały dwie rozjeżdżające się listy TODO).
- [x] Zdecydować o losie usuniętych plików w `docs/architecture/` (diagramy `.drawio.svg`, `dependencies.svg`, `classes/packages_cv_matcher.png`, `security_policies.md`) — **zrobione: nie odtwarzamy, `overview.md` zastępuje je opisem tekstowym** (decyzja i uzasadnienie per plik w `overview.md`, sekcja "Historia tego dokumentu").

## 4. Decyzje otwarte dla właściciela produktu/repo

1. **Result API — sync czy async?** Czy `/cv/upload` powinien móc opcjonalnie czekać (parametr `?sync=true`) na wynik Etapu B dla małych plików, czy zawsze tylko fire-and-forget + polling przez `/status`?
2. ~~**Kolejka w tle** — czy zostajemy przy `BackgroundTasks` (prostsze, ale bez trwałości) do MVP, czy inwestujemy teraz w Celery/Arq (Faza 4) przed pierwszym wdrożeniem produkcyjnym?~~ **Rozstrzygnięte: Celery + Redis**, patrz [`celery-roadmap.md`](./celery-roadmap.md).

---

**Jak korzystać z tej roadmapy:** odznaczaj `[x]` w miarę realizacji. Każda faza nadaje się na odrębny PR — Faza 1 (Result API) powinna wejść przed czymkolwiek innym, bo bez niej pipeline Etapu B pozostaje praktycznie niewidoczny dla konsumentów API.
