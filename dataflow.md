# Przepływ danych: upload CV → wyświetlenie na stronie

Dokument opisuje pełną ścieżkę danych w aplikacji — od wgrania pliku CV przez użytkownika, przez przetwarzanie backendowe, aż po wyrenderowanie wyniku na stronie.

**Mechanizm asynchroniczności:** wyłącznie wbudowane `BackgroundTasks` z FastAPI — brak Celery/Redis/kolejki/WebSocket/SSE. Frontend odpytuje endpoint wynikowy cyklicznie (`setTimeout` polling).

---

## 1. Frontend — wybór i wysyłka pliku

**`frontend/src/app/pages/UploadPage.tsx:1-45`**

- Pole `<input type="file" accept="application/pdf">` przechwytuje obiekt `File`.
- Po submisji wywoływane jest `useCvStore().upload(file)` (`frontend/src/store/cvStore.ts:45-57`).
- Po otrzymaniu odpowiedzi użytkownik jest przekierowywany na `/cv/:cvDocumentId`.

**`frontend/src/lib/api/client.ts:25-39`** — `uploadCv(file)`
- Buduje `FormData` z polem `file`, wysyła `POST {VITE_API_URL}/cv/upload` (multipart).
- Przy błędzie HTTP rzuca `ApiError` (parsuje `{detail}` albo używa `statusText`).

---

## 2. Backend — endpoint `POST /cv/upload`

**`backend/app/api/v1/routes/ingestion.py:37-69`** (zamontowany w `backend/app/api/v1/router.py:9-10`)

Kolejność działań w ramach jednego żądania:

1. **Synchronicznie** (await, blokuje odpowiedź): `ingestion_service.process_cv_document(file)` — zapis pliku + OCR/ekstrakcja tekstu (patrz krok 3).
2. Natychmiast wstawiany jest **pending** wiersz `CVStructuredData`:
   `repository.upsert_structured_record(cv_document_id=lake_record.id, structured_data=None, status="pending")` + `commit()` (linie 48-53).
   Dzięki temu frontend może od razu pollować po `cv_document_id` bez wyścigu z 404.
3. Ciężkie przetwarzanie heurystyczne jest zlecane jako zadanie w tle:
   `background_tasks.add_task(processing_service.process_and_store, lake_record.id, raw_text_record.raw_text)` (linie 55-59) — wykonuje się **po** wysłaniu odpowiedzi HTTP.
4. Odpowiedź: `CVIngestionResponse` (201) z `cv_document_id`, mime type, nazwą pliku, licznikami znaków/słów i surowym wyekstrahowanym tekstem (`backend/app/schema/ingestion_dto.py:10-17`).

---

## 3. Zapis pliku i ekstrakcja tekstu (OCR)

**`backend/app/services/cv_pipeline/extract/ingestion_service.py:29-77`** — `IngestionService.process_cv_document`

1. `StorageService.save_pdf_file(file)` (`extract/file_service.py:42-70`):
   - walidacja rozszerzenia `.pdf`,
   - odczyt treści z limitem rozmiaru (`_read_within_limit`),
   - weryfikacja integralności pliku (sygnatury bajtowe, `app.core.security`),
   - ścieżka zapisu wg daty (`DateBasedPathProvider`), zapis na dysk pod nazwą UUID.
2. `repository.create_lake_record(...)` → wiersz `CVDocumentLake` (id, oryginalna nazwa, ścieżka, rozmiar, mime type) — model `backend/app/models/cv_document.py:7-22` (flush, bez commit).
3. Ponowny odczyt bajtów pliku → `OCRService.process_document(content, mime_type)` (`extract/ocr_service.py:19-27`):
   - próba ekstrakcji tekstu cyfrowego przez `pdfplumber` dla **wszystkich stron** (`_extract_digital_text`, linie 29-50),
   - jeśli tekst jest zbyt krótki (`MIN_TEXT_LENGTH`) → fallback do OCR: `pdf2image.convert_from_bytes` → preprocessing obrazu (grayscale, autocontrast, sharpen) → `pytesseract.image_to_string` (linie 52-75),
   - wynik: `(raw_text, page_count)`.
4. Liczenie metryk tekstu (`_build_text_metrics`) → `repository.create_raw_text_record(...)` → wiersz `CVRawText` (`backend/app/models/cv_raw_text.py:10-38`): `raw_text`, `character_count`, `word_count`, `page_count`, `extraction_tool`, `metadata_json`.
5. `commit()` + `refresh()`. W razie wyjątku: rollback sesji + usunięcie pliku z dysku (linie 73-77).

**Stan po tym kroku:** zapisane `cv_document_lake` (metadane pliku) + `cv_raw_text` (surowy tekst) + (z kroku 2) `cv_structured_data` ze `status="pending"`, `structured_data=NULL`.

---

## 4. Przetwarzanie w tle — orkiestracja pipeline'u

**`backend/app/services/cv_pipeline/processing_service.py:22-53`** — `CVProcessingService.process_and_store(cv_document_id, raw_text)`

1. `orchestrator.process_cv(raw_text)` (async) — patrz krok 5.
2. Wyjątek → zapis `structured_data={}`, `status="failed"`, zakończenie.
3. Sukces → `build_unified_record(heuristic_result=result, validator=orchestrator.tech_stack_validator)` (krok 6) buduje finalny rekord.
4. Rekord jest przepuszczany przez `json.loads(json.dumps(record, default=str))`, by wymusić typy serializowalne do JSON (np. `date` → string).
5. `status="completed"`.
6. `_store(...)`: nowa sesja DB, `repository.upsert_structured_record(...)` **aktualizuje istniejący pending wiersz** po PK (`cv_repository.py:68-92`), commit.

---

## 5. Czyszczenie → normalizacja → ekstrakcja heurystyczna

**`backend/app/services/cv_pipeline/transform/pipeline.py:13-37`** — `CVPipelineOrchestrator.process_cv`

1. **Czyszczenie OCR** — `clean_ocr_text(raw_text)` (`transform/cleaning.py:47-56`):
   - normalizacja unicode (NFC),
   - `ftfy.fix_text` + naprawa "mojibake" (polskie `ż` błędnie odczytane przez OCR),
   - usuwanie szumu graficznego (serie bulletów/myślników, artefakty `(cid:N)`),
   - normalizacja białych znaków, kolaps 3+ nowych linii do 2.
2. **Normalizacja** — `CVTextNormalizer.normalize_text(...)` (`transform/normalization.py`).
3. **Ekstrakcja heurystyczna** — `heuristic_manager.extract_all(normalized_text)`.

> Pipeline jest obecnie **czysto heurystyczny — bez LLM** (dosłowny komentarz w kodzie), mimo że schema/DTO wciąż modelują pole `FieldSource = "llm" | "merged"` na przyszłość.

---

## 6. Manager ekstrakcji heurystycznej

**`backend/app/services/cv_pipeline/transform/heuristic/manager.py:62-186`** — `HeuristicExtractionManager.extract_all`

- Regexy: `extract_email`, `extract_phones`, `extract_date_ranges`.
- `FlashLookupEngine.extract_matches(raw_text)` — dopasowania słownikowe (tech stack + stanowiska) metodą zbliżoną do Aho-Corasick.
- **Segmentacja** — `find_sections(raw_text)` (`heuristic/segmentation.py:83-112`): wykrywa nagłówki sekcji (doświadczenie/edukacja/certyfikaty/języki/umiejętności/projekty/podsumowanie, PL+EN) i zwraca ich zasięgi (offsety). Brak wykrytych sekcji → cały dokument traktowany jako sekcja "experience".
- Zakresy dat z offsetami (`extract_date_ranges_with_offsets`) — zachowywane tylko te leżące w sekcji "experience" (zapobiega wyciekom dat z edukacji/certyfikatów do historii zatrudnienia).
- `ExperienceService.calculate_experience(...)` → łączny staż (miesiące/lata).
- **Alokacja** (`heuristic/allocation.py`):
  - `allocate_matches_to_nearest_preceding_anchor` — przypisuje każde dopasowanie technologii do najbliższego poprzedzającego zakresu dat (stanowiska).
  - `pick_nearest_label_per_anchor` — dobiera tytuł stanowiska do zakresu dat metodą najmniejszej odległości (greedy, unikalne przypisania).
- `_build_work_experience_candidates` (linie 129-185) składa per okres pracy: `start_date`, `end_date`, `is_current`, `job_title`, `skills_used` (`{name, category}`).
- Dodatkowo (niezależnie od sekcji): `certifications`, `languages`, `education_field_of_study`, `soft_skill_tags` (slugowane tagi).

Wynik: słownik `{email, phones, dates, tech_stack, job_titles, total_experience_months, total_experience_years, certifications, languages, education_field_of_study, work_experience_candidates, soft_skill_tags}`.

---

## 7. Budowa finalnego, zunifikowanego rekordu

**`backend/app/services/cv_pipeline/transform/merge.py:195-231`** — `build_unified_record(heuristic_result, validator)`

- Każdy kandydat z `work_experience_candidates` → `WorkExperienceDto` (`job_title → role`, daty jako `"YYYY-MM"`, `end_date="Present"` jeśli trwa, `company=None`, `responsibilities=[]`).
- `seniority_estimate` z `total_experience_months`: `<24mo → junior`, `<72mo → mid`, inaczej `senior`.
- Walidacja/kanonizacja skilli względem słownika tech (`TechStackValidator.validate_skills`, synonimy → nazwa kanoniczna).
- `build_hard_skills` — liczy `months_used`/`last_used` per skill, scalając nakładające się okresy pracy (`merge_overlapping_ranges`), tag `source: "heuristic"`.
- `build_flat_tech_stack` — zwalidowana, zdeduplikowana lista płaska.
- `_build_education_from_heuristic` — jednoelementowa lista `education` z wypełnionym tylko `field_of_study`.

**Finalny kształt** (zgodny ze schemą `CVStructuredRecord`):

```json
{
  "summary": null,
  "total_experience_months": 0,
  "seniority_estimate": "junior|mid|senior",
  "work_experience": [
    {"company": null, "role": "...", "start_date": "YYYY-MM", "end_date": "YYYY-MM|Present|null", "is_current": true, "responsibilities": [], "skills_used": ["..."]}
  ],
  "skills": {
    "hard": [{"name": "...", "months_used": 0, "last_used": "...", "source": "heuristic"}],
    "soft": ["..."],
    "all_tech_stack_flat": ["..."]
  },
  "education": [{"institution": null, "degree": null, "field_of_study": "...", "graduation_year": null}],
  "languages": [{"language": "...", "level": "..."}],
  "certifications": ["..."],
  "validation": {"warnings": []}
}
```

(`transform/slug.py:18-30` — normalizacja nazw tagów używana w słownikach soft-skills, nie w samym `merge.py`.)

---

## 8. Zapis finalnego wyniku do bazy

Powrót do `processing_service.py:44-48`: rekord (po serializacji JSON) zapisywany przez `CVRepository.upsert_structured_record` — **aktualizuje** istniejący pending wiersz po PK, ustawia `status="completed"` (lub `"failed"`), `processed_at=now()`.

### Model bazy danych

**`backend/app/models/cv_structured_data.py:10-30`** — tabela `cv_structured_data`:
- `cv_document_id: UUID` — PK **i** FK do `cv_document_lake.id` (relacja 1:1).
- `structured_data: dict | None` — `JSONB`.
- `status: str` — domyślnie `"pending"`, wartości: `pending | completed | partial | failed`.
- `processed_at: datetime`.

Powiązane tabele: `cv_document_lake` (`backend/app/models/cv_document.py`), `cv_raw_text` (`backend/app/models/cv_raw_text.py`) — ten sam `UUID` co lake id.

---

## 9. Backend — endpoint odczytu wyniku

**`backend/app/api/v1/routes/ingestion.py:87-125`** — `GET /cv/{cv_document_id}/structured`

- `repository.get_structured_by_lake_id(...)`.
- 404 jeśli wiersz nie istnieje wcale (nie powinno się zdarzyć normalnie, bo pending wiersz jest wstawiany synchronicznie przy uploadzie).
- Walidacja `structured_data` wg pydantic `CVStructuredRecord` (`backend/app/schema/cv_structured_record.py`); błąd walidacji (np. stary format) → 500 z opisem (guard `_reject_unrecognized_shape`).
- Odpowiedź: `CVStructuredDataResponse{cv_document_id, status, structured_data, processed_at}` — `structured_data=null` przy `status="pending"`.
- **Brak WebSocket/SSE** — wyłącznie polling.

---

## 10. Frontend — polling i renderowanie wyniku

**`frontend/src/store/cvStore.ts:59-116`** — `fetchResult(cvDocumentId)`

- Ustawia `results[id] = {status: "loading"}`, wywołuje `getCvStructured` (`client.ts:41-49`).
- `status: "pending"` (200) → stan `"pending"`, retry przez `setTimeout` co `POLL_INTERVAL_MS=3000`, max `POLL_MAX_ATTEMPTS=100` (~5 min).
- HTTP 404 → traktowane jak `"pending"` i również retry.
- `status: "completed"/"failed"/"partial"` → `{status: "success", data}` (uwaga: nawet backendowy `"failed"` mapowany jest na frontendowe `"success"`, bo sprawdzany jest tylko sukces HTTP, nie pole `data.status` poza jawnym `"pending"`).
- Inny błąd → `{status: "error", error: message}`.

**`frontend/src/app/pages/CvResultPage.tsx:6-38`**

- Odczytuje `cvDocumentId` z URL, wywołuje `fetchResult` przy montowaniu, `stopPolling` przy odmontowaniu.
- Renderowanie:
  - `"Ładowanie..."` — podczas `loading`/undefined,
  - `"Przetwarzanie CV, proszę czekać..."` — podczas `pending`,
  - komunikat błędu — jeśli `error`,
  - przy `success` — **całość `entry.data` wypisywana jako sformatowany JSON w `<pre>`** (linie 29-33). Obecnie **nie istnieje dedykowany UI** do prezentacji pól (doświadczenie, skille itd.) — to surowy podgląd JSON.

---

## Diagram skrócony (kolejność kroków)

1. `UploadPage.tsx` → `uploadCv()` → `POST /cv/upload` (multipart)
2. `ingestion.py` → `IngestionService.process_cv_document` (await):
   a. `StorageService.save_pdf_file` → plik na dysku + `CVDocumentLake`
   b. `OCRService.process_document` → pdfplumber / fallback Tesseract
   c. `CVRepository.create_raw_text_record` → `CVRawText`, commit
3. Route wstawia pending `CVStructuredData` (`status="pending"`), commit
4. Route zleca `BackgroundTasks.add_task(process_and_store, ...)`, zwraca 201
5. Frontend → `/cv/:id`, `CvResultPage` zaczyna pollować `GET /cv/{id}/structured` co 3 s
6. (W tle, po odpowiedzi) `CVProcessingService.process_and_store`:
   a. `CVPipelineOrchestrator.process_cv`: `clean_ocr_text` → `normalize_text` → `HeuristicExtractionManager.extract_all` (segmentacja + słowniki + alokacja dat)
   b. `build_unified_record` (merge.py) → finalny `CVStructuredRecord`
   c. `CVRepository.upsert_structured_record` → `status="completed"`/`"failed"`, commit
7. Kolejny poll frontend'u dostaje `status != "pending"` → zapisuje i renderuje surowy JSON w `CvResultPage`
