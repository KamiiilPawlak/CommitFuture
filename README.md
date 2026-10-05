<p align="center">
  <img src="logo-cf.png" alt="CommitFuture logo" width="160" />
</p>

# CommitFuture — CV AI Matcher

System dopasowujący kandydatów do ofert pracy na podstawie treści CV, przetwarzanego lokalnie przez pipeline OCR + heurystyka + LLM. W repozytorium zaimplementowana jest dziś strona CV: upload PDF → OCR → ekstrakcja ustrukturyzowanych danych → zapis wyniku. Strona ofert pracy (scraping + matching) ma na razie jedynie szkielet modelu danych.

Pełny opis architektury: [`docs/architecture/overview.md`](docs/architecture/overview.md) (oraz szczegóły pipeline'u w [`docs/architecture/cv-etl-pipline.md`](docs/architecture/cv-etl-pipline.md)).

## Stack

**Backend**
- Python 3.11+, FastAPI, Pydantic v2
- SQLModel / SQLAlchemy + PostgreSQL, Alembic (migracje)
- Ekstrakcja tekstu: PyMuPDF, pdfplumber, Tesseract OCR, pdf2image
- LLM: Ollama (`qwen2.5:3b`) jako lokalny serwer wnioskowania

**Frontend**
- React 19 + TypeScript, Vite
- Tailwind CSS, Radix UI / shadcn

**DevOps / jakość kodu**
- Docker & Docker Compose
- Ruff, mypy, pylint, bandit, pre-commit
- pytest (pytest-asyncio, pytest-cov)
- MkDocs (dokumentacja serwowana jako statyczna strona)

## Architektura — komponenty (`docker-compose.yml`)

| Serwis | Port | Rola |
| --- | --- | --- |
| `api` | 8000 | FastAPI — cała logika biznesowa (`backend/app`) |
| `postgres` | 5432 | Baza `cv_ai_matcher` |
| `ollama` | 11434 | Lokalny serwer LLM, przy starcie sam pobiera model `qwen2.5:3b` |
| `mkdocs` | 8001 | Statyczna dokumentacja z katalogu `docs/` |

Pliki PDF trzymane są na dysku (`storage/cv_uploads/`), nie w obiektowym storage.

## Wymagania

- Docker + Docker Compose
- Do pracy bez kontenerów: Python 3.11+, [`uv`](https://github.com/astral-sh/uv), Node.js 20+, zainstalowany lokalnie Tesseract OCR

## Szybki start (Docker)

```powershell
# Windows (PowerShell) — buduje obrazy i odpala docker-compose up
./run.ps1

# wymuszenie przebudowania obrazów bez cache
./run.ps1 -Action build -NoCache
```

albo bezpośrednio:

```bash
docker compose up --build
```

Po starcie:
- API: http://localhost:8000 (dokumentacja Swagger: `/docs`)
- Dokumentacja (MkDocs): http://localhost:8001

## Konfiguracja

Backend czyta ustawienia z `backend/.env` (patrz `backend/app/core/config.py`). Minimalny zestaw zmiennych:

```
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

Dodatkowe opcje konfiguracyjne (z wartościami domyślnymi w kodzie): `MAX_FILE_SIZE`, `ALLOWED_MIME_TYPES`, `TESSERACT_CMD` (ścieżka do binarki Tesseract — ustaw, jeśli nie jest dostępna w `PATH`, np. na Windows), `OLLAMA_BASE_URL`, `OLLAMA_MODEL_NAME`, `OLLAMA_TIMEOUT`, `OLLAMA_MAX_RETRIES`.

## Praca lokalna bez Dockera

**Backend**

```bash
cd backend
uv pip install --system .[dev]
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

## Testy i jakość kodu

```bash
cd backend
pytest
ruff check .
mypy .
```

Pre-commit hooki (ruff, formatowanie, lint commitów przez `commitlint.config.js`) są skonfigurowane w `.pre-commit-config.yaml` — włącz je lokalnie przez `pre-commit install`.

## Struktura repozytorium

```
backend/        # FastAPI, pipeline OCR/ETL/LLM, modele, repozytoria, testy
frontend/       # React + Vite SPA
docs/           # Dokumentacja architektury (MkDocs)
storage/        # Pliki CV zapisywane na dysku (runtime, nie commitowane)
docker-compose.yml
run.ps1         # Skrypt startowy dla Windows/PowerShell
checklist.md    # Lista TODO wg priorytetów
```

## Status projektu

Projekt jest w aktywnym rozwoju. Aktualny stan funkcjonalny, znane braki i plan prac znajdują się w [`checklist.md`](checklist.md) oraz [`docs/architecture/roadmap.md`](docs/architecture/roadmap.md).
