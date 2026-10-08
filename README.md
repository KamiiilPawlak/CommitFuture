<p align="center">
  <img src="logo-cf.png" alt="CommitFuture logo" width="160" />
</p>

<h1 align="center">CommitFuture</h1>

<p align="center">
  System dopasowujący kandydatów do ofert pracy na podstawie treści CV, przetwarzanego lokalnie przez pipeline OCR + ekstrakcja heurystyczna (słowniki, segmentacja sekcji, <b>bez LLM</b>).
</p>

<p align="center">
  <a href="docs/architecture/overview.md"><b>Architektura</b></a> ·
  <a href="docs/architecture/cv-etl-pipline.md">Pipeline CV</a> ·
  <a href="checklist.md">Checklist</a> ·
  <a href="docs/architecture/roadmap.md">Roadmap</a>
</p>

<p align="center">
  W repozytorium zaimplementowana jest dziś strona CV: upload PDF → OCR → ekstrakcja ustrukturyzowanych danych → zapis wyniku → odczyt wyniku przez API.
  Strona ofert pracy (scraping + matching) ma na razie jedynie szkielet modelu danych. Frontend to na razie samodzielny szkielet SPA (React + Vite), jeszcze niepodłączony do API.
</p>

---

## Stack

<table>
<tr>
<td valign="top" width="33%">

**Backend**

- Python 3.11+, FastAPI, Pydantic v2
- SQLModel / SQLAlchemy + PostgreSQL, Alembic
- PyMuPDF, pdfplumber, Tesseract OCR, pdf2image
- Ekstrakcja ustrukturyzowanych danych: heurystyka (słowniki + regex + segmentacja sekcji, `backend/app/services/cv_pipeline/transform/heuristic/`), **bez LLM**

</td>
<td valign="top" width="33%">

**Frontend**

- React 19, TypeScript, Vite
- Tailwind CSS v4, shadcn/ui, Radix UI
- Husky + lint-staged + commitlint
- ESLint, Prettier, Knip
- Jest + Testing Library

</td>
<td valign="top" width="33%">

**DevOps / jakość kodu**

- Docker & Docker Compose
- Ruff, mypy, pylint, bandit, pre-commit
- pytest (pytest-asyncio, pytest-cov)
- MkDocs (statyczna dokumentacja)

</td>
</tr>
</table>

## Architektura — komponenty (`docker-compose.yml`)

<table>
<tr><th>Serwis</th><th>Port</th><th>Rola</th></tr>
<tr><td><code>api</code></td><td>8000</td><td>FastAPI — cała logika biznesowa (<code>backend/app</code>)</td></tr>
<tr><td><code>postgres</code></td><td>5432</td><td>Baza <code>cv_ai_matcher</code></td></tr>
<tr><td><code>mkdocs</code></td><td>8001</td><td>Statyczna dokumentacja z katalogu <code>docs/</code></td></tr>
</table>

Pliki PDF trzymane są na dysku (`storage/cv_uploads/`), nie w obiektowym storage.

Kluczowe endpointy: `POST /api/v1/cv/upload` (zapis + OCR, ekstrakcja heurystyczna w tle) oraz `GET /api/v1/cv/{cv_document_id}/structured` (odczyt statusu i wyniku ustrukturyzowanych danych).

## Wymagania

- Docker + Docker Compose
- Do pracy bez kontenerów: Python 3.11+, [`uv`](https://github.com/astral-sh/uv), Node.js 20+, zainstalowany lokalnie Tesseract OCR

## Szybki start

<details open>
<summary><b>🪟 Windows (PowerShell)</b></summary>

```powershell
# Domyślny start (sprawdzenie/budowanie obrazów + uruchomienie kontenerów)
./run.ps1

# Wymuszone przebudowanie obrazów bez cache
./run.ps1 build -ForceBuild -NoCache

# Czyszczenie środowiska i artefaktów
./run.ps1 clean

# Uruchomienie frontendu (npm run dev), niezależnie od backendu
./run.ps1 frontend

# Uruchomienie backendu (uvicorn) i frontendu (npm run dev) razem, każdy w nowym oknie PowerShell
./run.ps1 start

# Narzędzia jakości kodu: backend + frontend / tylko backend / tylko frontend
./run.ps1 quality
./run.ps1 quality-backend
./run.ps1 quality-frontend
```

</details>

<details>
<summary><b>🐧 Linux / macOS (bash)</b></summary>

```bash
# Nadaj uprawnienia wykonania (jednorazowo)
chmod +x run.sh scripts/*.sh

# Domyślny start
./run.sh

# Wymuszone przebudowanie bez cache
./run.sh build --force-build --no-cache

# Czyszczenie środowiska
./run.sh clean

# Uruchomienie frontendu (npm run dev), niezależnie od backendu
./run.sh frontend

# Narzędzia jakości kodu: backend + frontend / tylko backend / tylko frontend
./run.sh quality
./run.sh quality-backend
./run.sh quality-frontend
```

</details>

<details>
<summary><b>🐳 Bezpośrednio przez Docker Compose</b></summary>

```bash
docker compose up --build
```

</details>

Po starcie:

- API: <http://localhost:8000> (dokumentacja Swagger: `/docs`)
- Dokumentacja (MkDocs): <http://localhost:8001>

## Konfiguracja

Backend czyta ustawienia z `backend/.env` (patrz `backend/app/core/config.py`). Minimalny zestaw zmiennych:

```env
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

Dodatkowe opcje konfiguracyjne (z wartościami domyślnymi w kodzie): `MAX_FILE_SIZE`, `ALLOWED_MIME_TYPES`, `TESSERACT_CMD` (ścieżka do binarki Tesseract — ustaw, jeśli nie jest dostępna w `PATH`, np. na Windows).

## Praca lokalna bez Dockera

<details>
<summary><b>Backend</b></summary>

```bash
cd backend
uv pip install --system .[dev]
uvicorn app.main:app --reload
```

</details>

<details>
<summary><b>Frontend</b></summary>

```bash
cd frontend
npm install
npm run dev
```

Po starcie SPA jest dostępne pod adresem wypisanym przez Vite (domyślnie <http://localhost:5173>).

</details>

## Testy i jakość kodu

<details>
<summary><b>Backend</b></summary>

```bash
cd backend
pytest
ruff check .
mypy .
```

</details>

<details>
<summary><b>Frontend</b></summary>

```bash
cd frontend
npm run test          # testy jednostkowe (Jest + Testing Library)
npm run lint           # ESLint
npm run format:check   # sprawdzenie formatowania (Prettier)
npm run knip           # wykrywanie nieużywanego kodu/zależności
```

</details>

Pre-commit hooki (ruff, formatowanie, lint commitów przez `commitlint.config.js`) są skonfigurowane w `.pre-commit-config.yaml` — włącz je lokalnie przez `pre-commit install`. Dla `frontend/` git hooki (lint-staged + commitlint) są skonfigurowane przez Husky i instalują się automatycznie po `npm install` (skrypt `prepare`) — przy każdym commicie uruchamiają ESLint i Prettier na zmienionych plikach.

## Struktura repozytorium

```text
backend/        # FastAPI, pipeline OCR/ETL (ekstrakcja heurystyczna), modele, repozytoria, testy
frontend/       # React + Vite SPA
docs/           # Dokumentacja architektury (MkDocs)
storage/        # Pliki CV zapisywane na dysku (runtime, nie commitowane)
docker-compose.yml
run.ps1         # Skrypt startowy dla Windows/PowerShell
run.sh          # Skrypt startowy dla Linux/macOS (bash)
scripts/        # Skrypty pomocnicze (build, cleanup) dla run.ps1 / run.sh
checklist.md    # Lista TODO wg priorytetów
```

## Status projektu

Projekt jest w aktywnym rozwoju. Aktualny stan funkcjonalny, znane braki i plan prac znajdują się w [`checklist.md`](checklist.md) oraz [`docs/architecture/roadmap.md`](docs/architecture/roadmap.md).
