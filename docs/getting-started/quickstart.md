# Szybki Start (Quickstart)

Ten przewodnik przeprowadzi Cię przez proces pierwszego uruchomienia pełnego stosu aplikacyjnego (API, baza danych, Ollama) oraz wykonania pierwszego zapytania testowego (parsowanie pliku PDF/CV).

---

## 1. Przygotowanie pliku konfiguracyjnego

Przed pierwszym uruchomieniem skopiuj szablon zmiennych środowiskowych `.env.example` do pliku `.env`:

"Linux"

```bash
cp .env.example .env
```

### Windows

```powershell
Copy-Item .env.example .env
```

!!! note "Domyślna konfiguracja"
Domyślne wartości w `.env.example` są gotowe do działania w środowisku deweloperskim. Więcej o poszczególnych parametrach przeczytasz w sekcji [Konfiguracja .env](configuration.md).

---

## 2. Uruchomienie aplikacji

Skorzystaj z dedykowanych skryptów uruchomieniowych, które automatycznie zbudują obrazy Docker oraz podniosą wszystkie wymagane kontenerowe usługi.

### Linux

```bash
./run.sh
```

### Windows

```powershell
.\run.ps1
```

### Co dzieje się w tle?

1. Budowany jest obraz Docker aplikacji API zawierający `Python`, `uv`, `Tesseract OCR` oraz `Poppler`.
2. Uruchamiana jest baza danych PostgreSQL, menedżer kolekcji Redis oraz usługa lokalnego modelu LLM (**Ollama**).

---

## 3. Weryfikacja stanu usług (Healthcheck)

Upewnij się, że wszystkie usługi wystartowały poprawnie.

- **Swagger UI / Interaktywna Dokumentacja API:**
  Otwórz w przeglądarce adres: [http://localhost:8000/docs](http://localhost:8000/docs)

```

```
