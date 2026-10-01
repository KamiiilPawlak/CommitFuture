# Konfiguracja zmiennych środowiskowych (.env)

Aplikacja wykorzystuje bibliotekę **`pydantic-settings`** do ładowania, walidacji i typowania zmiennych środowiskowych. Pozwala to na pełną kontrolę nad spójnością typów (np. liczby całkowite, wartości bolowskie, adresy URL) już na etapie uruchamiania serwera.

---

## 1. Jak działa zarządzanie konfiguracją?

Zmienne są definiowane w klasie `Settings` (zlokalizowanej w `src/core/config.py`). Klasa ta automatycznie odczytuje wartości z następujących źródeł z zachowaniem priorytetu:

1. **Zmienne środowiskowe systemu/kontenera** _(najwyższy priorytet)_
2. **Plik `.env`** _(w katalogu głównym projektu)_
3. **Domyślne wartości zdefiniowane w kodzie** _(najniższy priorytet)_

!!! tip "Walidacja typów"
Jeśli podasz nieprawidłowy typ (np. tekst zamiast portu liczbowego w `POSTGRES_PORT`), aplikacja wygeneruje czytelny błąd podczas startu i bezpiecznie przerwie działanie.

---

## 2. Katalog Zmiennych Środowiskowych

Poniżej znajduje się pełna lista zmiennych obsługiwanych przez system wraz z ich domyślnymi wartościami.

### Ustawienia Ogólne i API (`AppConfig`)

| Zmienna        |  Typ   | Domyślna wartość  | Opis                                                                |
| :------------- | :----: | :---------------: | :------------------------------------------------------------------ |
| `PROJECT_NAME` | `str`  | `"CV Parser ETL"` | Nazwa projektu widoczna w dokumentacji OpenAPI.                     |
| `ENVIRONMENT`  | `str`  |  `"development"`  | Środowisko uruchomieniowe (`development`, `staging`, `production`). |
| `DEBUG`        | `bool` |      `true`       | Tryb debugowania (szczegółowe komunikaty błędów w API).             |
| `API_V1_STR`   | `str`  |    `"/api/v1"`    | Prefiks ścieżek dla wersji v1 API.                                  |
| `SECRET_KEY`   | `str`  |    _wymagane_     | Tajny klucz do szyfrowania tokenów JWT / sesji.                     |

### Baza Danych PostgreSQL (`DatabaseSettings`)

| Zmienna             |  Typ  | Domyślna wartość | Opis                                                              |
| :------------------ | :---: | :--------------: | :---------------------------------------------------------------- |
| `POSTGRES_SERVER`   | `str` |      `"db"`      | Host bazy danych (nazwa usługi w Docker Compose lub `localhost`). |
| `POSTGRES_PORT`     | `int` |      `5432`      | Port bazy danych PostgreSQL.                                      |
| `POSTGRES_USER`     | `str` |   `"postgres"`   | Nazwa użytkownika bazy danych.                                    |
| `POSTGRES_PASSWORD` | `str` |   `"postgres"`   | Hasło do bazy danych.                                             |
| `POSTGRES_DB`       | `str` |  `"cv_parser"`   | Nazwa bazy danych.                                                |
| `DATABASE_URL`      | `str` |   _generowana_   | Asynchroniczny URL połączenia (`postgresql+asyncpg://...`).       |

### Usługa LLM — Ollama (`OllamaSettings`)

| Zmienna              |   Typ   |    Domyślna wartość     | Opis                                                                    |
| :------------------- | :-----: | :---------------------: | :---------------------------------------------------------------------- |
| `OLLAMA_BASE_URL`    |  `str`  | `"http://ollama:11434"` | Adres URL serwera Ollama.                                               |
| `OLLAMA_MODEL`       |  `str`  |      `"llama3.2"`       | Model językowy używany do ekstrakcji i walidacji danych z CV.           |
| `OLLAMA_TIMEOUT`     | `float` |         `60.0`          | Limit czasu (w sekundach) na odpowiedź z LLM przed zgłoszeniem wyjątku. |
| `OLLAMA_MAX_RETRIES` |  `int`  |           `3`           | Liczba ponowień próby wywołania w przypadku błędu walidacji JSON.       |

### Silnik OCR — Tesseract (`OCRSettings`)

| Zmienna                |  Typ   | Domyślna wartość | Opis                                                                       |
| :--------------------- | :----: | :--------------: | :------------------------------------------------------------------------- |
| `TESSERACT_LANGUAGES`  | `str`  |   `"pol+eng"`    | Języki używane do rozpoznawania tekstu (oddzielone separatorem `+`).       |
| `OCR_DPI`              | `int`  |      `300`       | Rozdzielczość (DPI) przy konwersji stron PDF na obrazy.                    |
| `OCR_FALLBACK_ENABLED` | `bool` |      `true`      | Czy uruchamiać OCR, gdy z pliku PDF nie uda się wyciągnąć tekstu natywnie. |

---

## 3. Kod źródłowy Pydantic Settings (`src/core/config.py`)

Poniżej znajduje się fragment implementacji pokazuje strukturę walidacji w kodzie Python:

```python
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    PROJECT_NAME: str = "CV Parser ETL"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change_this_in_production_secret_key"

    # Database
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "cv_parser"

    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Ollama
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT: float = 60.0

    # OCR
    TESSERACT_LANGUAGES: str = "pol+eng"
    OCR_DPI: int = 300
    OCR_FALLBACK_ENABLED: bool = True


settings = Settings()
```
