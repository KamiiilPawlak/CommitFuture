# Migracje (Alembic)

Dokument opisuje konfigurację Alembica wdrożoną w `backend/` i sposób pracy z migracjami. Wcześniej schemat był tworzony wyłącznie przez `SQLModel.metadata.create_all()` (`app/db/database.py:init_db`) — bez historii zmian i bez kontrolowanego sposobu modyfikacji istniejących tabel z danymi. `celery-migration-checklist.md` odnotowywało to jako świadomie odłożone zadanie — ten dokument opisuje jego realizację.

## Struktura

```
backend/
├── alembic.ini
└── alembic/
    ├── env.py            — konfiguracja środowiska migracji
    ├── script.py.mako    — szablon nowych plików migracji
    └── versions/
        └── 1691a8e1f341_initial_schema.py
```

## Jak `env.py` jest podłączony do aplikacji

`alembic/env.py` nie używa statycznego URL z `alembic.ini` — bierze go z tej samej konfiguracji co aplikacja:

```python
from app.core.config import settings
import app.models  # rejestruje wszystkie modele w SQLModel.metadata

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
target_metadata = SQLModel.metadata
```

Konsekwencje:

- Migracja łączy się zawsze z bazą wskazaną przez `DATABASE_URL` z `.env` (ten sam mechanizm, co reszta aplikacji) — nie trzeba osobno konfigurować URL w `alembic.ini`.
- `--autogenerate` widzi te same modele, które widzi aplikacja (import `app.models` ładuje `CVDocumentLake`, `CVRawText`, `CVStructuredData`, `JobPosting`), więc diff liczony jest względem rzeczywistych klas SQLModel, nie względem ręcznie przepisanego metadata.
- Żeby zadziałać na innej bazie niż ta z `.env`, trzeba nadpisać zmienną środowiskową `DATABASE_URL` przed odpaleniem komendy (pydantic-settings czyta najpierw env var, potem plik `.env`).

## Codzienna praca z migracjami

Wszystkie komendy odpalane z katalogu `backend/`, w wirtualnym środowisku projektu.

**Nowa migracja po zmianie modelu w `app/models/`:**

```bash
alembic revision --autogenerate -m "opis zmiany"
```

Zawsze **przeczytać wygenerowany plik** w `alembic/versions/` przed odpaleniem — autogenerate wykrywa różnice w strukturze, ale nie wie nic o istniejących danych (patrz sekcja "Pułapka" niżej).

**Zastosowanie migracji (do najnowszej):**

```bash
alembic upgrade head
```

**Sprawdzenie aktualnej wersji bazy:**

```bash
alembic current
```

**Wycofanie jednej migracji:**

```bash
alembic downgrade -1
```

## Pułapka: `NOT NULL` na tabeli z danymi

Migracja `1691a8e1f341_initial_schema` dodaje kolumnę `cv_structured_data.recovery_attempts` (wprowadzoną do modelu wcześniej, w ramach mechanizmu odzyskiwania zawieszonych zadań — patrz `app/services/cv_pipeline/recovery.py`). Model definiuje `default=0`, ale to jest **domyślna wartość w Pythonie**, nie w bazie — `--autogenerate` z tego wygenerował:

```python
op.add_column('cv_structured_data', sa.Column('recovery_attempts', sa.Integer(), nullable=False))
```

Taki `ALTER TABLE ... ADD COLUMN ... NOT NULL` **wysypuje się na tabeli z istniejącymi wierszami** (Postgres nie ma czym wypełnić starych rekordów). Poprawka — dopisanie `server_default`:

```python
op.add_column('cv_structured_data', sa.Column('recovery_attempts', sa.Integer(), nullable=False, server_default='0'))
```

`server_default` jest wartością bazodanową, egzekwowaną podczas samego `ALTER TABLE` — dzięki temu istniejące wiersze dostają `0`, a nowe wiersze i tak korzystają z `default=0` zdefiniowanego w modelu SQLModel.

**Zasada na przyszłość:** przy każdym `add_column` z `nullable=False` na tabeli, która może mieć dane — sprawdzić, czy model ma `default`, i jeśli tak, przenieść go też do `server_default` w migracji. Autogenerate tego nie robi automatycznie.

## Status zastosowania

Migracja `1691a8e1f341` została zweryfikowana i zastosowana:

- na lokalnej bazie testowej (`commit_future_test`) — z symulowanym stanem "przed migracją" (kolumna usunięta, przykładowy wiersz wstawiony) — kolumna dodana poprawnie, istniejący wiersz dostał `recovery_attempts=0`,
- na lokalnej bazie dev (`commit_future`, 33 istniejące wiersze w `cv_structured_data`) — zastosowana bez błędów, wszystkie wiersze dostały `recovery_attempts=0`.

## Co zostało poza zakresem

- **CI/CD** — uruchamianie `alembic upgrade head` automatycznie (np. przy starcie kontenera `api`) nie jest skonfigurowane; dziś to ręczny krok.
- `init_db()` / `SQLModel.metadata.create_all()` nie zostało usunięte z kodu — nowe środowiska (świeża baza) wciąż mogą dostać schemat tą drogą. Docelowo powinno to zostać zastąpione przez `alembic upgrade head` jako jedyny sposób tworzenia schematu, żeby historia migracji była źródłem prawdy dla każdej bazy (w tym świeżej) — patrz `celery-roadmap.md` Faza 5.
