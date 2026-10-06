# Checklist / Roadmapa — CommitFuture

Roadmapa oparta na faktycznym stanie kodu opisanym w `docs/architecture/cv-etl-pipline.md` (Etap A — Ingestion jest podłączony do API, Etap B — ETL/NLP działa tylko w testach). Priorytety ustawione pod kątem: najpierw spiąć pipeline end-to-end, potem domknąć bezpieczeństwo/jakość, na końcu porządki.

## P0 — Połączenie pipeline'u (bez tego ETL/NLP jest martwym kodem)

- [x] Podłącz `CVPipelineOrchestrator.process_cv` do przepływu po zapisie `cv_raw_text` — endpoint lub zadanie w tle (np. BackgroundTasks/Celery/worker) wywołujące Etap B po Etapie A.
- [x] Zaprojektuj i dodaj tabelę/model **"Structured CV"** (kandydat, doświadczenie, edukacja, umiejętności, `llm_result`) — dziś brakuje miejsca docelowego dla wyniku `process_cv`.
- [x] Zapisuj wynik `CVPipelineOrchestrator.process_cv` do nowej tabeli zamiast zwracania go tylko z pojedynczego wywołania.
- [x] Zweryfikuj/uzupełnij `ProcessedCVTO` (`app/schema/ingestion_dto.py`) — jest zdefiniowane, ale nieużywane; albo wykorzystaj je jako DTO odpowiedzi, albo usuń jeśli zbędne.

## P1 — Bezpieczeństwo i walidacja uploadu

- [x] Podłącz `verify_file_integrity()` (`app/core/security.py`, magic bytes przez `python-magic`) do `StorageService.save_pdf_file` lub routera uploadu — dziś walidacja opiera się wyłącznie na rozszerzeniu pliku.
- [x] Wyegzekwuj `settings.MAX_FILE_SIZE` (5 MB) w `StorageService` — dziś limit jest zdefiniowany, ale niesprawdzany, więc upload nie ma faktycznego limitu rozmiaru.
- [x] Rozważ przywrócenie/odtworzenie usuniętego `docs/architecture/adr/0001-magic-bytes-validation.md` (lub nowego ADR) opisującego decyzję o walidacji magic bytes, skoro mechanizm ma zostać podłączony.

## P2 — Jakość danych z pipeline'u

- [x] Dodaj walidację krzyżową LLM ↔ heurystyki (np. wykrywanie "halucynacji" LLM — e-mail/telefon zwrócony przez Ollamę, którego nie ma w `raw_text`).
- [x] Policz faktyczny `page_count` dla `cv_raw_text` (dziś zawsze `0`) — np. z `pdfplumber`/`pdf2image` przy ekstrakcji.
- [x] Dodaj retry (np. z backoffem) dla wywołania Ollamy w `OllamaLLMClient` — dziś błąd sieci/parsowania powoduje jednorazowy fallback na same heurystyki bez ponowienia.
- [x] Zdecyduj o losie `ExperienceService.calculate_experience` i `TechStackValidator` — albo podłącz je do pipeline'u (zamiast zduplikowanej logiki w `experience_calc.py` / samego `FlashLookupEngine`), albo usuń jako martwy kod pokryty tylko testami jednostkowymi.

## P3 — Przenośność / infrastruktura

- [x] Usuń zahardkodowaną ścieżkę `OCRConfig.TESSERACT_CMD` (Windows-only) — przenieś do zmiennej środowiskowej/configu, żeby działało w kontenerach/CI i na innych OS.
- [x] Sprawdź `backend/CommitFuture.egg-info/` w statusie gita (untracked) — jest w `.gitignore` (`*CommitFuture.egg-info`).

## P4 — Dokumentacja (w toku na tym branchu `docs/update-docs`)

- [x] Uzupełnij `docs/architecture/overview.md` — plik opisuje teraz architekturę ogólną (wcześniej był pusty).
- [x] Odtwórz ADR o walidacji magic bytes — `docs/architecture/adr/0001-magic-bytes-validation.md` istnieje.
- [ ] Zdecyduj, co zrobić z usuniętymi plikami w `docs/architecture/` (diagramy `.drawio.svg`, `dependencies.svg`, `classes/packages_cv_matcher.png`, `security_policies.md`) — czy zastępuje je `overview.md`/`cv-etl-pipline.md`, czy trzeba odtworzyć część z nich.
- [ ] Przenieś treść `security_policies.md` (zanim zniknie bezpowrotnie) do nowego dokumentu, jeśli opisane tam zasady są nadal aktualne — część z nich pokrywa się z punktami z sekcji P1 (magic bytes, limit rozmiaru pliku).

## P5 — Result API (największa luka wg `roadmap.md`, Faza 1)

- [x] Dodaj endpoint odczytu wyniku — `GET /api/v1/cv/{cv_document_id}/structured` zwraca `status` oraz `structured_data` z `cv_structured_data` (404 jeśli rekordu jeszcze nie ma); łączy w jednym endpointzie to, co `roadmap.md` opisywał jako dwa osobne (`/status` + `/result`).
- [ ] Test integracyjny end-to-end: upload → poczekaj na `BackgroundTasks` → `GET /{cv_document_id}/structured` zwraca dane zgodne z tym, co zapisał `CVProcessingService` (dziś testy pokrywają tylko `POST /cv/upload`, patrz `backend/tests/integration/api/test_cv_endpoints.py`).
- [ ] Oceń, czy `BackgroundTasks` wystarcza na produkcję, czy potrzebna jest trwała kolejka (Celery/Arq/RQ) z retry/DLQ niezależnym od życia procesu API — dziś restart serwera w trakcie przetwarzania zamraża rekord w `pending` bez mechanizmu odzyskania. Checklista przygotowawcza: [`docs/architecture/celery-migration-checklist.md`](docs/architecture/celery-migration-checklist.md).

## P6 — Frontend (branch `feat/init-frontend`)

- [x] Scaffolding SPA: React 19 + TypeScript + Vite, Tailwind CSS v4, shadcn/ui/Radix UI.
- [x] Husky + lint-staged + commitlint skonfigurowane dla `frontend/`.
- [x] `run.ps1 frontend` uruchamia `npm run dev` niezależnie od backendu.
- [ ] Podłącz frontend do API (`POST /cv/upload`, `GET /cv/{id}/structured`) — dziś SPA jest niepodłączonym szkieletem.
- [ ] Zdecyduj o konteneryzacji frontendu (dodanie serwisu do `docker-compose.yml`) albo pozostaniu przy uruchamianiu lokalnym (`npm run dev`).

---

**Źródło:** `docs/architecture/cv-etl-pipline.md`, sekcja "Braki / TODO wynikające z analizy kodu" (punkty 1–8) + stan `git log`/`git status` na branchu `feat/init-frontend` (2026-10-06) + `docs/architecture/roadmap.md` (Faza 1, sekcja P5) + `docs/architecture/celery-migration-checklist.md`.

Co dalej: zaznaczaj `[x]` w miarę realizacji albo powiedz mi, od którego punktu zaczynamy, a rozpiszę go na konkretne kroki/PR.
