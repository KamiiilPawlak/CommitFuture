# Instalacja środowiska

Projekt został zaprojektowany tak, aby zminimalizować wymagania dotyczące środowiska lokalnego. Wszystkie zależności systemowe (`tesseract`, `poppler`, `libmagic`) oraz biblioteki Python są automatycznie instalowane wewnątrz kontenera Docker.

---

## 1. Szybki start

Do zbudowania obrazu Docker i przygotowania pełnego środowiska służą przygotowane skrypty `run.sh` oraz `run.ps1`.

Linux (`run.sh`)

1. Nadaj uprawnienia do wykonywania skryptu (jednorazowo):

```bash
chmod +x run.sh
```

2. Uruchom budowanie środowiska i kontenerów:

```bash
./run.sh
```

"Windows PowerShell (`run.ps1`)"

Uruchom skrypt w oknie PowerShell:

```powershell
.\run.ps1
```

!!! tip "Uprawnienia do wykonywania skryptów w PowerShell"
Jeśli napotkasz błąd dotyczący polityki wykonywania skryptów (`ExecutionPolicy`), uruchom jednorazowo:

```powershell
 Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
        `
```

---

## 2. Wymagania wstępne

Niezależnie od wybranego systemu operacyjnego, na maszynie hosta wymagane są jedynie:

- **Docker** (wersja 20.10 lub nowsza / Docker Desktop na Windowsie)
- **Docker Compose** (wersja 2.0 lub nowsza)
- **Git**

---

## 3. Lokalny Development poza Dockerem

Jeśli planujesz rozwijać aplikację lokalnie na hoście bez kontenerów, musisz zainstalować zależności systemowe oraz pakiet `uv` bezpośrednio w systemie:

### Zależności systemowe

### Linux

```bash
    sudo apt update && sudo apt install -y \
        tesseract-ocr \
        tesseract-ocr-pol \
        tesseract-ocr-eng \
        poppler-utils \
        libmagic1
```

### Windows

**Rekomendowane:** Skorzystaj ze środowiska **WSL2 (Ubuntu)** i wykonaj kroki dla Linuksa. **Ręczna instalacja na Windows:** Wymaga ręcznego pobrania binariów Tesseract OCR oraz Poppler i dodania ich do zmiennej środowiskowej `PATH`.

### Linux Bash

```bash
uv venv
source .venv/bin/activate
uv pip sync pyproject.toml --extra dev
```

### Windows PowerShell

```PowerShell
uv venv
.\.venv\Scripts\activate
uv pip sync pyproject.toml --extra dev
```

---

## Kolejne kroki

- [Quickstart](quickstart.md)
