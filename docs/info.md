```text
repo/
├── mkdocs.yml
├── docs/
│   ├── index.md                     # co to jest, 1 diagram, linki
│   │
│   ├── getting-started/
│   │   ├── installation.md          # uv/pip, Tesseract, Poppler, libmagic
│   │   ├── quickstart.md            # docker compose up + pierwszy request
│   │   └── configuration.md         # wszystkie zmienne .env (pydantic-settings)
│   │
│   ├── architecture/
│   │   ├── overview.md              # C4 context + container (Mermaid)
│   │   ├── project-structure.md     # drzewo src/ i odpowiedzialność modułów
│   │   ├── data-flow.md             # end-to-end: request → ETL → DB
│   │   ├── tech-stack.md            # co i dlaczego (FastAPI, SQLModel, Ollama...)
│   │   └── decisions/               # ADR-y
│   │       ├── index.md
│   │       ├── 0001-sqlmodel-vs-sqlalchemy.md
│   │       ├── 0002-ollama-local-llm.md
│   │       └── template.md
│   │
│   ├── etl/
│   │   ├── index.md                 # koncepcja: Extract → Transform → Load, wspólny kontrakt
│   │   ├── common/                  # WSPÓŁDZIELONE ETAPY
│   │   │   ├── cleaning.md          # ftfy, regex, usuwanie szumu
│   │   │   ├── normalization.md     # phonenumbers, dateparser, unicode
│   │   │   ├── heuristics.md        # flashtext, reguły, scoring pewności
│   │   │   ├── llm-extraction.md    # prompty, retry, walidacja JSON
│   │   │   └── output-schema.md     # docelowy schema CV (Pydantic) + przykłady
│   │   ├── pdf-pipeline/
│   │   │   ├── overview.md          # diagram etapów
│   │   │   ├── ingestion.md         # upload, magic bytes, limity
│   │   │   ├── text-extraction.md   # pdfplumber / pymupdf – kiedy który
│   │   │   ├── ocr.md               # Tesseract, pdf2image, języki, fallback
│   │   │   └── error-handling.md
│   │   └── scraping-pipeline/       # PLANNED
│   │       ├── overview.md          # status: planowane
│   │       ├── sources.md
│   │       └── differences-from-pdf.md
│   │
│   ├── llm/
│   │   ├── ollama-setup.md          # modele, GPU, docker
│   │   ├── prompts.md               # wersjonowanie promptów
│   │   ├── evaluation.md            # deepeval, metryki, datasety
│   │   └── troubleshooting.md       # halucynacje, timeouty, niepoprawny JSON
│   │
│   ├── database/
│   │   ├── schema.md                # ER diagram (Mermaid erDiagram)
│   │   ├── migrations.md            # Alembic workflow
│   │   └── conventions.md           # naming, indeksy, async vs sync
│   │
│   ├── api/
│   │   ├── overview.md              # auth, błędy, paginacja, wersjonowanie
│   │   ├── endpoints.md             # opis biznesowy + przykłady curl
│   │   ├── errors.md                # katalog kodów błędów
│   │   └── openapi.md               # osadzony swagger lub link do /docs
│   │
│   ├── reference/                   # AUTO-GENEROWANE (mkdocstrings)
│   │   └── (generowane z src/)
│   │
│   ├── development/
│   │   ├── setup.md                 # środowisko dev, pre-commit
│   │   ├── code-quality.md          # ruff, mypy, pylint, bandit – konfiguracje
│   │   ├── testing.md               # pytest, testcontainers, schemathesis, piramida testów
│   │   ├── conventions.md           # Conventional Commits, branching, style
│   │   └── contributing.md
│   │
│   ├── operations/
│   │   ├── docker.md                # Dockerfile, compose, multi-stage, healthchecki
│   │   ├── deployment.md
│   │   ├── logging.md               # loguru – format, poziomy, korelacja requestów
│   │   └── runbook.md               # typowe awarie i co robić
│   │
│   ├── changelog.md
│   └── glossary.md                  # ETL, OCR, heurystyka, confidence...
│
└── scripts/
    └── gen_ref_pages.py             # generuje reference/ z src/

```
