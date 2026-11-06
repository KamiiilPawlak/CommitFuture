# Roadmapa — wdrożenie CI/CD w tym repo

> Stan na: 2026-10-14. Ten dokument rozpisuje **kolejność i zakres PR-ów** potrzebnych do realnego wdrożenia CI/CD — analogicznie do [`celery-roadmap.md`](./celery-roadmap.md). Zakłada się, że pojęcia z [`research/ci-cd-research.md`](../../research/ci-cd-research.md) (CI vs Delivery vs Deployment, strategie deploymentu) są już znane — tu jest tylko **plan działania** dla *tego* repo.
>
> Powiązane: [`research/ci-research.md`](../../research/ci-research.md) (CI — decyzje i szablon workflow już gotowe, niewdrożone), [`research/cd-research.md`](../../research/cd-research.md) (CD — darmowy stack Render+Neon+GitHub Pages, czysty research), [`research/alembic-research.md`](../../research/alembic-research.md) (migracje jako krok w pipeline CD), [`celery-roadmap.md`](./celery-roadmap.md) Faza 5 (wstrzymana — czeka na ten dokument).
>
> **Tryb realizacji:** jak w `celery-roadmap.md` — każda faza to jeden PR, zatwierdzany przez właściciela repo między fazami.

## 0. Stan wejściowy (co już jest zdecydowane/zrobione)

- [x] **CI, decyzja o bazie testowej:** Opcja B (testcontainers) zaimplementowana i zweryfikowana lokalnie (`tests/conftest.py` sam podnosi efemeryczny Postgres) — patrz `ci-research.md` sekcja 2. Zero pracy do powtórzenia tutaj.
- [x] **CI, szablon workflow:** gotowy do wklejenia, patrz `ci-research.md` sekcja 4 (`uv sync --locked --extra dev`, `ruff`, `mypy`, `pytest --cov`).
- [ ] **`.github/workflows/` nie istnieje w repo** — zero plików, mimo gotowego szablonu. To jest punkt startowy Fazy 1.
- [x] **CD, research stacku:** Render (backend) + Neon (Postgres) + GitHub Pages (frontend/docs) — w 100% darmowe, bez karty kredytowej, patrz `cd-research.md`. Zero kont/rejestracji zrobionych.
- [ ] **Alembic nie jest jeszcze wdrożony** (patrz `alembic-research.md`) — to blokuje Fazę 6 tej roadmapy (migracje w pipeline CD) i Fazę 5 `celery-roadmap.md`. Nie blokuje Faz 1–5 tutaj (CI i statyczny/manualny CD mogą wejść bez Alembica).

## 1. Fazy (każda = jeden PR)

### Faza 1 — CI: workflow backendu (bez zmian w kodzie aplikacji)

Cel: każdy PR i push na `main` odpala lint + type-check + testy, wynik widoczny jako status check.

- [ ] Dodać `.github/workflows/backend-ci.yml` z szablonu `ci-research.md` sekcja 4 (checkout → system deps apt → setup-python 3.11 → `astral-sh/setup-uv` → `uv sync --locked --extra dev` → `ruff check .` → `mypy app` → `pytest --cov`).
- [ ] Upewnić się, że `uv.lock` jest aktualny (`uv lock --check` albo po prostu `uv sync --locked` lokalnie przed PR-em) — `--locked` w workflow failuje job, jeśli nie jest.
- [ ] Włączyć w ustawieniach repo **branch protection** na `main`: required status check = job `test` z tego workflow. Bez tego CI tylko informuje, nie blokuje złych PR-ów.
- [ ] Zweryfikować na realnym PR (czerwony → poprawka → zielony), że mechanizm faktycznie blokuje merge przy czerwonym statusie.

### Faza 2 — CI: workflow frontendu (równoległy, niezależny)

Cel: frontend ma własny, szybki feedback, niezależny od Postgresa/backendu.

- [ ] Nowy job (albo nowy workflow) `frontend-ci.yml`: `npm ci && npm run lint && npm run test && npm run build`.
- [ ] `working-directory: frontend` (analogicznie do `defaults.run.working-directory: backend` w szablonie backendu).
- [ ] Dodać też jako required status check na `main`.

### Faza 3 — CI: porządki z listy w `ci-research.md` sekcja 4

Cel: domknąć otwarte punkty z istniejącego researchu, zanim przejdziemy do CD.

- [ ] Cache `uv` (`actions/cache` na `~/.cache/uv`) — szybszy feedback na PR.
- [ ] `concurrency:` group per branch/PR, żeby kilka pushów pod rząd nie mnożyło równoległych runów.
- [ ] Health-check/weryfikacja, że `services:`/testcontainers faktycznie nie są potrzebne na runnerze GitHub-hosted (Docker jest tam preinstalowany) — potwierdzić jednym realnym przebiegiem, nie tylko teoretycznie.

### Faza 4 — Decyzja: Continuous Delivery czy Continuous Deployment?

Cel: rozstrzygnąć pytanie otwarte z `ci-cd-research.md` sekcja 8, **przed** pisaniem workflow CD — inaczej Faza 5 nie wie, czy ma dodać bramkę `environment` z required reviewer, czy nie.

- [ ] Decyzja właściciela repo: push na `main` = automatyczny deploy (Continuous Deployment) **albo** automatyczny build + manualne "zatwierdź deploy" (Continuous Delivery, przez GitHub `environment` z protection rule).
- [ ] Jeśli Delivery: utworzyć `environment` (np. `production`) w ustawieniach repo z `required reviewers`.
- [ ] Zapisać decyzję i jej uzasadnienie w `cd-research.md` (dziś ten dokument nie rozstrzyga tego explicite).

### Faza 5 — CD: backend (Render) + baza (Neon)

Cel: pierwszy realny, automatyczny deploy backendu — zależny od zielonego CI z Fazy 1 (`needs:` między jobami/workflowami).

- [ ] Konto Render + Neon (darmowe, bez karty kredytowej, patrz `cd-research.md` sekcja 2–3).
- [ ] Neon: baza produkcyjna, `DATABASE_URL` jako secret w GitHub (albo bezpośrednio jako env var w Render, jeśli deploy idzie przez natywną integrację Render↔GitHub, nie przez Actions).
- [ ] Render: Web Service z `backend/Dockerfile`, połączony z Neonem.
- [ ] Workflow `deploy-backend.yml`: trigger `push` na `main`, `needs: [backend-ci]` (albo `workflow_run` jeśli CI jest osobnym workflow) — deploy **tylko** po zielonym CI.
- [ ] Jeśli Faza 4 = Continuous Delivery: krok deployu idzie przez `environment: production` z wymaganą akceptacją.
- [ ] Health check po deployu: `GET /` albo dedykowany `/health` (do sprawdzenia, czy istnieje — jeśli nie, dodać minimalny endpoint) odpytywany po deployu, zanim job się oznaczy jako sukces.

### Faza 6 — CD: migracje schematu w pipeline (zależne od wdrożenia Alembica)

**Blokowane przez:** wdrożenie Alembica (patrz `alembic-research.md`) — ta faza nie ma sensu, dopóki `alembic/` nie istnieje w repo.

- [ ] Krok `alembic upgrade head` **przed** restartem/deployem nowej wersji API (patrz `alembic-research.md` sekcja 8 i `ci-cd-research.md` sekcja 7 — pułapka "stary i nowy kod na chwilę równolegle na tej samej bazie").
- [ ] Zdecydować: migracje jako osobny krok w tym samym workflow deployu, czy jako release phase/start command na Render (zależnie od tego, co platforma wspiera bez dodatkowego kosztu).
- [ ] Test: deploy z migracją, która dodaje kolumnę `nullable=True` — potwierdzić, że stary kod (przed deployem) nie wywala się na nowej kolumnie w trakcie przełączania.

### Faza 7 — CD: frontend + docs (GitHub Pages)

Cel: statyczny deploy, niezależny od backendu/bazy — może wejść równolegle z Fazą 5, nie musi czekać.

- [ ] Workflow `deploy-frontend.yml`: `npm run build` → `actions/deploy-pages`.
- [ ] Workflow (albo krok) `mkdocs gh-deploy` dla `docs/` (patrz `cd-research.md` sekcja 5).
- [ ] Oba triggerowane na `push` do `main`, bez zależności od zielonego CI backendu (frontend ma własny CI z Fazy 2).

## 2. Co NIE jest w tej roadmapie (świadomie odłożone)

- **Self-hosted runnery** — niepotrzebne, GitHub-hosted (`ubuntu-latest`) wystarcza w pełni na obecną skalę (patrz `ci-cd-research.md` słownik: Runner).
- **Matrix build** (wiele wersji Pythona/OS) — jeden target (`python:3.11-slim`) wystarcza, repo nie jest biblioteką publikowaną pod wiele wersji.
- **Canary/blue-green deployment** — Render darmowy tier nie daje takiej kontroli nad ruchem; `Recreate`/`Rolling` natywne dla platformy wystarczają na tym etapie (patrz `ci-cd-research.md` sekcja 7). Do rozważenia tylko, jeśli projekt kiedyś przejdzie na infrastrukturę z pełną kontrolą (np. Kubernetes) — nie dziś.
- **Celery worker w CD** (`celery-roadmap.md` Faza 5) — osobna, już opisana faza, odblokowana przez tę roadmapę (po Fazie 5–6 tutaj) plus Alembica.

## 3. Kryterium "zrobione"

CI/CD jest wdrożone, gdy: każdy PR dostaje automatyczny, blokujący status check (lint+testy, backend i frontend osobno), a push na `main` prowadzi do zweryfikowanego, powtarzalnego deployu (automatycznego albo z jedną manualną akceptacją — zależnie od decyzji z Fazy 4) bez ręcznego SSH/kopiowania plików.
