# 1. Walidacja bezpieczenstwa plikow za pomoca Magic Bytes

**Status:** Zaakceptowany i wdrożony
**Data:** 2026-06-01
**Autor:** Kamil

## Kontekst i Problem

Aplikacj CV AI Matcher pozwala uzytkownikom na przesylanie dokumentow aplikacyjnych w formacie PDF. Istnieje ryzyko, ze zlosliwy uzytkownik sporbuje przeslac plik wykonywalny (np. `.exe`, `.bat`) lub skrypt, zmieniajac jedynie jego rozszerzenie na `.pdf`(np. `wirus.pdf`).

Poleganie wylacznie na walidacji rozszerzenai pliku dostarczonego w naglowku HTTP Context-Type jest niewystarczajace oraz niebezpieczne.

## Rozważane Opcje

1. **Walidacja wyłącznie po rozszerzeniu pliku (.pdf):** Najszybsza w implementacji, ale bardzo łatwa do obejścia.
2. **Użycie zewnętrznego skanera antywirusowego (np. ClamAV):** Maksymalne bezpieczeństwo, ale wprowadza ogromny narzut wydajnościowy i dodatkową infrastrukturę do utrzymania.
3. **Weryfikacja sygnatury binarnej (Magic Bytes):** Odczytanie pierwszych kilku bajtów strumienia pliku bezpośrednio w pamięci przed zapisem na dysk i dopasowanie ich do oficjalnego wzorca dla formatu PDF (`%PDF-` / `25 50 44 46`).

## Decyzja

Wybieramy **Opcję 3 (Weryfikacja sygnatury binarnej - Magic Bytes)**. Logika ta zostanie zaimplementowana asynchronicznie w module `app/core/security.py`. Każdy przesyłany plik zostanie sprawdzony na poziomie nagłówka binarnego przed dopuszczeniem do dalszego przetwarzania przez potok ingestion.

## Konsekwencje

- **Pozytywne:** Skuteczna ochrona przed podstawowymi atakami typu Extension Spoofing; brak narzutu wydajnościowego (sprawdzamy tylko pierwsze bajty).
- **Negatywne:** W przypadku chęci rozszerzenia aplikacji o obsługę plików `.docx` lub `.rtf` w przyszłości, będziemy musieli ręcznie rozbudować słownik dozwolonych sygnatur binarnych w `security.py`.

## Status wdrożenia

`verify_file_integrity()` (`app/core/security.py`) jest od tej aktualizacji wywoływana z `StorageService.save_pdf_file()` (`app/services/ingestion_service/file_service.py`), zaraz po walidacji rozmiaru pliku i przed zapisem na dysk. Wcześniej funkcja istniała w kodzie, ale nie była podłączona do żadnego przepływu — ta decyzja była zaakceptowana, lecz niewdrożona.
