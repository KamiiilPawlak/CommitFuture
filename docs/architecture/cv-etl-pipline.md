# CV ETL Pipeline

Dokumentacja opisuje faktyczny stan implementacji w `backend/app` (stan na podstawie kodu, nie założeń). W projekcie istnieją **dwa oddzielne, niepołączone ze sobą etapy przetwarzania**:

- **Etap A — Ingestion** (`app/services/ingestion_service/`): upload pliku → walidacja → zapis do Data Lake → OCR/ekstrakcja tekstu → zapis surowego tekstu do bazy. Jest podłączony do API (`POST /api/v1/cv/upload`).
- **Etap B — ETL/NLP** (`app/services/etl_cv_service/`): czyszczenie tekstu → normalizacja → ekstrakcja heurystyczna → parsowanie przez LLM (Ollama). Logika jest gotowa i pokryta testami integracyjnymi, ale **nie jest jeszcze wywoływana z żadnego endpointu API** ani zapisywana do bazy — `CVPipelineOrchestrator` jest dziś uruchamiany wyłącznie w testach (`backend/tests/integration/test_pipeline.py`).

## Diagram przepływu (stan faktyczny)

```text
ETAP A — INGESTION (podłączony do API, POST /api/v1/cv/upload)
================================================================
Upload (UploadFile)
↓
StorageService.save_pdf_file  — walidacja rozszerzenia .pdf, odrzucenie pustego pliku
↓
CVRepository.create_lake_record  — rekord w cv_document_lake (Data Lake)
↓
OCRService.process_document
   ├─ pdfplumber: próba ekstrakcji tekstu cyfrowego
   └─ jeśli tekst < MIN_TEXT_LENGTH → fallback: pdf2image + pytesseract (OCR)
↓
CVRepository.create_raw_text_record  — rekord w cv_raw_text (surowy tekst + metryki)
↓
CVIngestionResponse  — odpowiedź HTTP 201 z surowym tekstem i metadanymi


ETAP B — ETL / NLP (NIEPODŁĄCZONY do API — wywoływany dziś tylko w testach)
================================================================
raw_text (np. z cv_raw_text.raw_text)
↓
clean_ocr_text()            — cleaning.py: naprawa mojibake, usuwanie szumu, whitespace
↓
CVTextNormalizer.normalize_text()  — normalization.py: daty, telefony, linki, poziomy językowe
↓
HeuristicExtractionManager.extract_all()  — regexy + słowniki (email, telefon, daty, tech, stanowiska)
↓
OllamaLLMClient.parse_cv()  — lokalny LLM (Ollama) zwraca CvLlmDto (JSON Schema wymuszony przez Ollamę)
↓
dict: {..wynik heurystyk.., "llm_result": CvLlmDto | None}
   (brak dalszego zapisu do bazy — wynik nie trafia obecnie do "Structured DB")
```

---

## ETAP A — Ingestion

### 1. Upload

**Plik:** `app/api/v1/routes/ingestion.py`, `app/services/ingestion_service/ingestion_service.py`

- Endpoint: `POST /api/v1/cv/upload`, przyjmuje plik jako `UploadFile` (`multipart/form-data`).
- Router (`ingestion.py`) odpowiada tylko za warstwę HTTP: wywołuje `IngestionService.process_cv_document`, mapuje wyjątki na kody HTTP.
- Cała logika zapisu i walidacji jest w `IngestionService` / `StorageService`, nie w routerze.

**Mapowanie błędów w routerze:**

| Wyjątek          | Kod | Sytuacja                                             |
| ---------------- | --- | ---------------------------------------------------- |
| `ValueError`     | 400 | zły format pliku, pusty plik, błąd zapisu na dysk    |
| inny `Exception` | 500 | nieoczekiwany błąd w procesie ETL                    |
| sukces           | 201 | plik przyjęty, zapisany i przetworzony (OCR + zapis) |

**Odpowiedź (`CVIngestionResponse`, `app/schema/ingestion_dto.py`):** `cv_document_id`, `mime_type`, `original_name`, `character_count`, `word_count`, `raw_text`, `message`.

### 2. Walidacja pliku

**Plik:** `app/services/ingestion_service/file_service.py` (`StorageService.save_pdf_file`)

Faktyczne kontrole wykonywane przed zapisem:

1. **Nazwa i rozszerzenie:** `file.filename` musi istnieć i kończyć się na `.pdf` (case-insensitive) — inaczej `ValueError` → 400.
2. **Niepusty plik:** odczytana zawartość (`await file.read()`) musi mieć rozmiar > 0 bajtów — inaczej `ValueError` → 400.
3. **Błąd zapisu na dysk:** przechwycony i opakowany w `ValueError` → 400 (nie 500 — patrz niżej, "Uwaga").

**Czego NIE sprawdza dziś `StorageService`:**

- Nie ma kontroli limitu rozmiaru pliku w `StorageService` (ustawienie `settings.MAX_FILE_SIZE = 5 MB` istnieje w `app/core/config.py`, ale nie jest tu wykorzystywane).
- Nie ma sprawdzania magic bytes/MIME w locie uploadu. Funkcja `verify_file_integrity()` (`app/core/security.py`), która sprawdza prawdziwy MIME pliku przez `python-magic` względem `settings.ALLOWED_MIME_TYPES` (`application/pdf`, `image/png`, `image/jpeg`), **istnieje, ale nie jest wywoływana nigdzie w aplikacji** (ani w routerze, ani w serwisach) — jest to dead code / zadanie do podłączenia.

**Czego nie ufamy:** rozszerzenia i oryginalnej nazwy pliku, bo kontroluje je klient — dlatego na dysku plik dostaje własną nazwę `<uuid>.pdf`, a oryginalna nazwa jest zapisywana tylko jako metadana w `cv_document_lake.original_filename`.

### 3. Raw DataLake (zapis fizyczny + metadane)

**Pliki:** `app/services/ingestion_service/storage_path_provider.py`, `file_service.py`, `app/models/cv_document.py`

- `DateBasedPathProvider` zapisuje pliki w katalogu `storage/cv_uploads/<nazwa_miesiąca_pl>/` (np. `storage/cv_uploads/pazdziernik/`), tworząc katalog w razie potrzeby.
- Plik zapisywany jest pod unikalną nazwą `<uuid4><rozszerzenie>`.
- Oryginał nigdy nie jest modyfikowany — kolejne etapy operują na bajtach odczytanych z dysku (`StorageService.read_file`) lub na tekście.
- Metadane trafiają do tabeli `cv_document_lake` (model `CVDocumentLake`): `id` (UUID), `original_filename`, `storage_path`, `file_size_bytes`, `mime_type` (domyślnie `application/pdf`, w praktyce brany z `UploadFile.content_type`), `created_at`.
- Przy błędzie w dalszych krokach (OCR, zapis do bazy) transakcja jest wycofywana (`repository.rollback()`), a fizyczny plik usuwany (`file_service.delete_file`) — patrz `IngestionService.process_cv_document`, blok `except`.

### 4. Ekstrakcja tekstu (OCR / tekst cyfrowy)

**Plik:** `app/services/ingestion_service/ocr_service.py` (`OCRService`)

- Jeśli `mime_type == "application/pdf"`: najpierw próba ekstrakcji tekstu cyfrowego przez `pdfplumber` (strona po stronie, z wczesnym przerwaniem po przekroczeniu `OCRConfig.MIN_TEXT_LENGTH = 100` znaków).
- Jeśli tekst cyfrowy jest pusty lub krótszy niż próg → fallback na OCR: `pdf2image.convert_from_bytes` renderuje strony do obrazów, `pytesseract.image_to_string` (język `pol+eng`) wykonuje OCR.
- Przed OCR obraz jest przetwarzany filtrami PIL: konwersja do skali szarości, `autocontrast`, opcjonalnie `SHARPEN` (`OCRConfig.APPLY_SHARPEN = True`).
- Dla typów innych niż PDF (np. `image/png`, `image/jpeg`) ekstrakcja idzie od razu przez ścieżkę OCR.
- Operacja OCR jest synchroniczna (`pytesseract`/`pdf2image`), uruchamiana w osobnym wątku przez `asyncio.to_thread`, by nie blokować event loopa.
- **Zależność zewnętrzna:** ścieżka do binarki Tesseract jest zahardkodowana w `OCRConfig.TESSERACT_CMD` (`C:\Program Files\Tesseract-OCR\tesseract.exe`) — działa tylko na Windows z lokalnie zainstalowanym Tesseractem; brak konfiguracji przez zmienną środowiskową.

**Wejście:** bajty pliku + `mime_type`. **Wyjście:** surowy tekst (`str`).

### 5. Zapis surowego tekstu

**Pliki:** `app/services/ingestion_service/ingestion_service.py`, `app/models/cv_raw_text.py`

- `IngestionService._build_text_metrics` liczy `character_count` i `word_count` (prosty `len(text.split())`) oraz buduje `metadata_json` ze statusem (`"empty"` / `"success"`).
- Zapis do tabeli `cv_raw_text` (model `CVRawText`, klucz główny = `cv_document_id`, FK do `cv_document_lake.id`): `raw_text`, `character_count`, `word_count`, `page_count` (dziś zawsze `0` — liczba stron nie jest jeszcze liczona), `extraction_tool` (stała wartość `"pdfplumber/pytesseract"`), `metadata_json` (JSONB), `extracted_at`.
- Repozytorium: `app/repositories/cv_repository.py` (`CVRepository`) — `create_lake_record`, `create_raw_text_record`, `get_lake_by_id`, `get_raw_text_by_lake_id`, `commit`/`rollback`/`refresh`.

---

## ETAP B — ETL / NLP (`app/services/etl_cv_service/`)

> Status: logika kompletna i testowana (`backend/tests/integration/test_pipeline.py`, `backend/tests/services/etl_cv/...`), ale orchestrator **nie jest wywoływany z żadnego endpointu** i wynik nie jest dziś zapisywany do bazy jako "Structured CV". To naturalny kolejny krok integracyjny (patrz sekcja "Braki / TODO").

Punkt wejścia: `CVPipelineOrchestrator.process_cv(raw_text: str)` (`pipeline.py`). Kroki wewnątrz wykonywane są sekwencyjnie dla czyszczenia/normalizacji/heurystyki, a wywołanie LLM jest opakowane w `try/except` — błąd Ollamy **nie przerywa** pipeline'u, tylko pomija `llm_result` (`None`) i zwraca sam wynik heurystyk.

### 6. Cleaning

**Plik:** `app/services/etl_cv_service/cleaning.py` (`clean_ocr_text`)

Deterministyczne, bezstanowe czyszczenie tekstu (ten sam tekst wejściowy zawsze daje ten sam wynik):

1. `_normalize_unicode` — normalizacja Unicode do formy NFC.
2. `_repair_ocr_mojibake` — naprawa typowych błędów kodowania z `ftfy.fix_text`, plus dodatkowa heurystyka regexowa, która wstawia polskie `ż` w miejscach pojedynczego "dziwnego" znaku między literami lub na początku słowa (np. artefakty OCR dla `ż`/`rz`).
3. `_remove_graphic_noise` — usuwa ciągi ≥3 znaków graficznych (`-_.*•■♦` itp.), wzorce `(cid:123)` (typowy artefakt ekstrakcji z PDF), pojedyncze znaki-punktory (`■♦•:-`).
4. `_normalize_whitespace` — zwija powtórzone białe znaki/taby do pojedynczej spacji, przycina każdą linię, redukuje ≥3 kolejne nowe linie do dokładnie dwóch (pusty wiersz między akapitami).

**Wejście/wyjście:** `str → str`. Pusty tekst wejściowy daje pusty string.

### 7. Normalization

**Plik:** `app/services/etl_cv_service/normalization.py` (`CVTextNormalizer`)

Kolejność transformacji w `normalize_text`:

1. `_normalize_punctuation` — warianty myślników Unicode → `-`; warianty cudzysłowów (`„” « »`) → `"`.
2. `_normalize_dates` — trzy wzorce dat sprowadzane do `YYYY-MM`:
   - `MM/YYYY` lub `MM.YYYY` → `YYYY-MM`,
   - `YYYY/MM` lub `YYYY.MM` → `YYYY-MM`,
   - data słowna PL/EN (np. "styczeń 2022", "March 2021") → parsowana przez `dateparser` (`languages=["pl", "en"]`, `PREFER_DAY_OF_MONTH=first`) do `YYYY-MM`; przy błędzie parsowania fallback na `{rok}-01`.
   - frazy oznaczające trwającą pracę ("obecnie", "teraz", "aktualnie", "present", "do dziś" itd.) → literał `PRESENT`.
3. `_normalize_phone_numbers` — ze stringów pasujących do wzorca telefonu usuwane są spacje, myślniki i nawiasy (samo oczyszczenie formatu, bez walidacji numeru — walidacja numeru dzieje się dopiero w heurystyce, krok 8).
4. `_normalize_hyperlinks` — linki do GitHub/LinkedIn (`https://www.linkedin.com/in/...` itp.) sprowadzane do skróconej postaci `linkedin.com/in/...` / `github.com/...` (usunięcie protokołu i `www.`).
5. `_normalize_language_levels` — poziomy językowe typu `b2`, `c 1` → ujednolicone do `B2`, `C1` (wielka litera + cyfra bez spacji).
6. Na końcu: redukcja wielokrotnych spacji/tabów do pojedynczej spacji.

**Uwaga:** ten moduł **nie zmienia** struktury tekstu (nie dzieli na sekcje) — wyłącznie normalizuje zapis dat/telefonów/linków/poziomów w miejscu.

### 8. Heuristic extraction

**Plik:** `app/services/etl_cv_service/heuristic/manager.py` (`HeuristicExtractionManager.extract_all`)

Ekstrakcja regułowa, bez LLM — szybka, darmowa, deterministyczna, służy też jako "siatka bezpieczeństwa" do walidacji wyniku LLM (patrz Braki/TODO — porównanie z LLM nie jest dziś zaimplementowane).

| Dana                      | Moduł                                                     | Mechanizm                                                                                                                                                                                                                                                                       |
| ------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `email`                   | `heuristic/extractors/emails.py`                          | regex `[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}`, pierwsze dopasowanie, lowercase                                                                                                                                                                                                        |
| `phones`                  | `heuristic/extractors/phone.py`                           | `phonenumbers.PhoneNumberMatcher` (region domyślny `PL`), tylko numery uznane za `is_valid_number`, format E.164, deduplikacja                                                                                                                                                  |
| `dates`                   | `heuristic/extractors/dates.py`                           | regex na zakresy dat (`2021-2023`, `01.2020 - obecnie` itd.) + `dateparser` do parsowania pojedynczych dat; zwraca listę `{start_date, end_date, is_current}`                                                                                                                   |
| `tech_stack`              | `heuristic/dictionary/lookup_engine.py` + `tech_stack.py` | `FlashLookupEngine` oparty o `flashtext.KeywordProcessor` (case-insensitive, obsługa `+ # . -` i polskich znaków jako część słowa) dopasowuje aliasy do nazw kanonicznych (np. `"js"`, `"ecmascript"` → `"JavaScript"`)                                                         |
| `job_titles`              | `heuristic/dictionary/job_titles.py`                      | ten sam `FlashLookupEngine` (połączony słownik tech+stanowiska), dopasowania filtrowane po kluczach słownika stanowisk                                                                                                                                                          |
| `total_experience_months` | `heuristic/domain/experience_calc.py`                     | zakresy dat → pary `(start, end)` (brak końca lub `is_current=True` → `end = dzisiaj`; dla podanego miesiąca koniec = ostatni dzień tego miesiąca) → scalenie nakładających się przedziałów (`merge_overlapping_ranges`) → suma dni / `30.4375` zaokrąglona do pełnych miesięcy |

Dla pustego/`None` tekstu wejściowego `extract_all` zwraca od razu wartości domyślne (`email=None`, puste listy, `total_experience_months=0`) bez uruchamiania żadnych ekstraktorów.

**Niewykorzystany moduł pokrewny:** `heuristic/domain/experience_service.py` (`ExperienceService.calculate_experience`) liczy pełne `ExperienceMetrics` (dni/miesiące/lata/zakres dat) z tej samej logiki co `experience_calc.py`, ale nie jest wywoływany przez `HeuristicExtractionManager` ani orchestrator — używany jest tylko bezpośrednio w testach jednostkowych (`tests/unit/test_experience_service.py`). Podobnie `dictionaries/validator.py` (`TechStackValidator`), który normalizuje listę umiejętności względem słownika JSON (`dictionaries/tech_stack.json`), nie jest podłączony do pipeline'u — dziś normalizacja tech stacku idzie wyłącznie przez `FlashLookupEngine`.

### 9. LLM (Ollama)

**Pliki:** `app/services/etl_cv_service/llm/client.py` (`OllamaLLMClient`), `llm/prompts.py`, `app/schema/cv_llm.py` (`CvLlmDto`)

- Klient wysyła `POST {OLLAMA_BASE_URL}/api/chat` do lokalnej instancji Ollamy.
- Domyślna konfiguracja (`app/core/config.py`): `OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_MODEL_NAME=qwen2.5:3b`, `OLLAMA_TIMEOUT=90.0`, `temperature=0.0`, `stream=False`.
- Pole `format` w zapytaniu to wprost `CvLlmDto.model_json_schema()` — Ollama jest zmuszona zwrócić JSON zgodny ze schematem Pydantic (constrained generation), co eliminuje większość błędów parsowania.
- Prompt systemowy (`SYSTEM_PROMPT` w `prompts.py`) wymusza: zachowanie oryginalnego języka wpisów, `null`/`[]` dla brakujących danych, wyczerpujące wypisanie `hard_skills`, odpowiedź wyłącznie jako czysty JSON.
- Odpowiedź parsowana przez `CvLlmDto.model_validate_json(content)`.
- **Obsługa błędów:** `httpx.HTTPError` (sieć/HTTP) → `RuntimeError`; błąd walidacji Pydantic odpowiedzi → `ValueError`. Oba wyjątki są łapane wyżej, w `CVPipelineOrchestrator.process_cv`, i tylko logowane jako ostrzeżenie — **nie ma dziś automatycznego retry** ani fallbacku innego niż "kontynuuj z samą heurystyką".

**Schemat `CvLlmDto`** (`app/schema/cv_llm.py`): `personal_info` (imię, email, telefon, lokalizacja, LinkedIn), `summary`, `hard_skills: list[str]`, `soft_skills: list[str]`, `work_experience: list[WorkExperienceDto]` (firma, rola, daty, obowiązki), `projects: list[ProjectDto]`, `education: list[EducationDto]`, `languages: list[LanguageDto]`, `certifications: list[str]`.

### 10. Wynik końcowy

`CVPipelineOrchestrator.process_cv` zwraca jeden `dict`:

```python
{
    "email": str | None,
    "phones": list[str],
    "dates": list[dict],           # {start_date, end_date, is_current}
    "tech_stack": list[str],
    "job_titles": list[str],
    "total_experience_months": int,
    "llm_result": CvLlmDto | None, # None jeśli Ollama padła lub zwróciła niepoprawny JSON
}
```

Ten słownik nie jest dziś nigdzie zapisywany ani zwracany przez API — żyje wyłącznie w ramach pojedynczego wywołania `process_cv` (patrz test `test_cv_pipeline_orchestration`).

---

## Modele danych

| Model / Schema                       | Plik                          | Rola                                                                                                |
| ------------------------------------ | ----------------------------- | --------------------------------------------------------------------------------------------------- |
| `CVDocumentLake` (tabela)            | `app/models/cv_document.py`   | metadane fizycznego pliku w Data Lake                                                               |
| `CVRawText` (tabela)                 | `app/models/cv_raw_text.py`   | surowy tekst po OCR/ekstrakcji + metryki                                                            |
| `CVIngestionResponse`                | `app/schema/ingestion_dto.py` | odpowiedź endpointu `/cv/upload`                                                                    |
| `ExtractedMetadata`, `ProcessedCVTO` | `app/schema/ingestion_dto.py` | zdefiniowane DTO pod przyszły wynik ETL (sekcje + metadane); **nieużywane w kodzie poza definicją** |
| `CvLlmDto` + powiązane DTO           | `app/schema/cv_llm.py`        | kontrakt (i JSON Schema) wymuszany na odpowiedzi Ollamy                                             |
| `app/models/scraper.py`              | —                             | model powiązany z osobnym, niezależnym od tego pipeline'u obszarem (scraping)                       |

Brakuje tabeli / modelu na "Structured CV" (ustrukturyzowany, zwalidowany wynik LLM + heurystyk) — `ProcessedCVTO` w `ingestion_dto.py` wygląda na przygotowanie pod to, ale nie jest obecnie wypełniane ani zapisywane.

## Konfiguracja

**Plik:** `app/core/config.py` (`Settings`, `OCRConfig`)

| Ustawienie                  | Wartość domyślna                               | Uwagi                                                     |
| --------------------------- | ---------------------------------------------- | --------------------------------------------------------- |
| `MAX_FILE_SIZE`             | 5 MB                                           | zdefiniowane, ale nieużywane w `StorageService`           |
| `ALLOWED_MIME_TYPES`        | `pdf`, `png`, `jpeg`                           | używane tylko przez niepodłączone `verify_file_integrity` |
| `OLLAMA_BASE_URL`           | `http://localhost:11434`                       |                                                           |
| `OLLAMA_MODEL_NAME`         | `qwen2.5:3b`                                   |                                                           |
| `OLLAMA_TIMEOUT`            | 90 s                                           |                                                           |
| `DATABASE_URL`              | wymagane (bez wartości domyślnej)              | wczytywane z `.env`                                       |
| `OCRConfig.TESSERACT_CMD`   | `C:\Program Files\Tesseract-OCR\tesseract.exe` | ścieżka zahardkodowana pod Windows                        |
| `OCRConfig.MIN_TEXT_LENGTH` | 100 znaków                                     | próg decydujący o przejściu PDF → OCR                     |
| `OCRConfig.TESSERACT_LANG`  | `pol+eng`                                      |                                                           |
| `OCRConfig.APPLY_SHARPEN`   | `True`                                         | filtr wyostrzający przed OCR                              |

## Testy pokrywające pipeline

- `backend/tests/integration/test_pipeline.py` — pełen `CVPipelineOrchestrator.process_cv` na przykładowym CV.
- `backend/tests/integration/test_heuristic_manager.py`, `test_llm.py` — integracja heurystyk i klienta LLM.
- `backend/tests/integration/api/test_cv_endpoints.py`, `tests/api/v1/routes/test_ingestion.py` — endpoint `/cv/upload`.
- `backend/tests/services/etl_cv/cv_etl_service/` — `test_cleaning.py`, `test_normalization.py`, `heuristic/extractors/test_dates.py`, `test_email.py`, `test_phone.py`.
- `backend/tests/services/ingestion/test_ocr_service.py` — `OCRService`.
- `backend/tests/unit/` — pojedyncze ekstraktory, `test_experience_calc.py`, `test_experience_service.py`, `test_lookup_engine.py`, `test_tech_stack_validator.py`, `test_storage_path_provider.py`.

## Braki / TODO wynikające z analizy kodu

1. **Etap B nie jest podłączony do API** — brak endpointu/zadania w tle, które wywołuje `CVPipelineOrchestrator.process_cv` na tekście z `cv_raw_text` i zapisuje wynik.
2. **Brak "Structured DB"** — nie ma modelu/tabeli przechowującej ustrukturyzowany, zwalidowany wynik (dane kandydata, doświadczenie, edukacja, umiejętności) pod kątem wyszukiwania/matchingu.
3. **Brak walidacji krzyżowej LLM ↔ heurystyki** — opisana w pierwotnym pomyśle detekcja "halucynacji" LLM (np. e-mail z LLM, którego nie ma w tekście) nie jest zaimplementowana.
4. ~~**`verify_file_integrity` (magic bytes) i `TechStackValidator`** zdefiniowane, ale niepodłączone do przepływu~~ — `verify_file_integrity` jest już wywoływane w `StorageService.save_pdf_file` (`file_service.py:43`); `TechStackValidator` wciąż czeka na decyzję (patrz Faza 3 w `roadmap.md`).
5. ~~**`MAX_FILE_SIZE` nieegzekwowany**~~ — `StorageService.save_pdf_file` sprawdza rozmiar pliku przed zapisem i rzuca `ValueError` (`file_service.py:32-41`).
6. **`page_count` zawsze `0`** w `cv_raw_text` — liczba stron PDF nie jest dziś liczona.
7. **Brak retry dla Ollamy** — błąd sieci/parsowania LLM powoduje jednorazowy fallback na same heurystyki, bez ponowienia próby.
8. **`TESSERACT_CMD` zahardkodowany pod Windows** — brak przenośności na inne OS/kontenery bez zmiany kodu.
