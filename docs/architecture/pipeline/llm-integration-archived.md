# Integracja z LLM (Ollama) — zarchiwizowane

!!! warning "Kod usunięty z repozytorium"
    Ten moduł został **usunięty** z `backend/app/services/cv_pipeline/transform/llm/` (pliki `client.py`, `prompts.py`) oraz z `app/schema/cv_llm.py` (`CvLlmDto`, `PersonalInfoDto`, `ProjectDto`), bo ekstrakcja heurystyczna (słowniki + segmentacja sekcji + alokacja po offsetach, patrz `heuristic/manager.py`) przejęła całość tej funkcji bez potrzeby wywoływania modelu. Ta strona dokumentuje **jak to działało**, żeby można było łatwo odtworzyć integrację, jeśli przyszły przypadek użycia (np. nietypowe CV, których heurystyka nie obsłuży) będzie tego wymagał.

    DTO wspólne z `cv_llm.py` (`WorkExperienceDto`, `EducationDto`, `LanguageDto`) **zostały** w kodzie — są dziś używane jako wspólny kształt danych w `merge.py`, niezależnie od LLM.

## Dlaczego LLM był w pipeline

`CVPipelineOrchestrator.process_cv` wywoływał lokalny model przez Ollama **równolegle** do ekstrakcji heurystycznej (nie zamiast niej) — heurystyka działała jako podpowiedź (`heuristic_dates`, `heuristic_job_titles` w promptcie) i jako fallback, gdy LLM padł. Finalnie uznano, że przy dobrze zbudowanych słownikach i segmentacji sekcji heurystyka daje porównywalny wynik bez kosztu, opóźnienia i niedeterminizmu modelu.

## Konfiguracja (`app/core/config.py` → `Settings`)

| Ustawienie                      | Wartość domyślna         | Opis                                                      |
| -------------------------------- | ------------------------- | ----------------------------------------------------------- |
| `OLLAMA_BASE_URL`                | `http://localhost:11434` | Adres lokalnej instancji Ollama                             |
| `OLLAMA_MODEL_NAME`              | `qwen2.5:1.5b`            | Model użyty domyślnie w produkcji                           |
| `OLLAMA_NUM_THREAD`              | `4`                       | Liczba wątków CPU przekazywana do Ollamy (`options.num_thread`) |
| `OLLAMA_TEMPERATURE`             | `0.0`                     | Deterministyczne wyjście (constrained generation + temp=0)  |
| `OLLAMA_NUM_CTX`                 | `1024`                    | Rozmiar kontekstu modelu (tokeny)                            |
| `OLLAMA_TIMEOUT`                 | `200.0` s                 | Timeout pojedynczego żądania HTTP                            |
| `OLLAMA_MAX_RETRIES`             | `3`                       | Liczba prób przy błędzie sieci/HTTP                          |
| `OLLAMA_RETRY_BACKOFF_SECONDS`   | `1.0` s                   | Bazowy backoff, rosnący wykładniczo: `backoff * 2^(attempt-1)` |

W teście integracyjnym (`tests/integration/test_llm.py`, również usunięty) używano innej, mocniejszej wersji modelu do weryfikacji jakości: `qwen2.5:3b`, `timeout=90.0`.

`docker-compose.yml` (serwis `api`) przekazywał `OLLAMA_BASE_URL=http://host.docker.internal:11434` + `extra_hosts: host.docker.internal:host-gateway`, żeby kontener mógł dobić się do Ollamy uruchomionej na hoście (Ollama **nie była** własnym serwisem w `docker-compose.yml` — zawsze zakładano, że działa lokalnie na maszynie dewelopera).

## Payload wysyłany do Ollamy

Klient (`OllamaLLMClient.parse_cv`) wywoływał `POST {OLLAMA_BASE_URL}/api/chat`:

```json
{
  "model": "qwen2.5:1.5b",
  "messages": [
    { "role": "system", "content": "<SYSTEM_PROMPT, patrz niżej>" },
    { "role": "user", "content": "<prompt z promptu użytkownika, patrz niżej>" }
  ],
  "format": "<CvLlmDto.model_json_schema() - JSON Schema wymuszany na Ollamie>",
  "stream": false,
  "options": {
    "temperature": 0.0,
    "num_thread": 4,
    "num_ctx": 1024
  }
}
```

Pole `format` to **dosłownie** wynik `CvLlmDto.model_json_schema()` (Pydantic v2) — Ollama (model wspierający constrained/structured generation) jest zmuszona wygenerować JSON zgodny z tym schematem, co w praktyce eliminowało większość błędów parsowania po stronie klienta.

Odpowiedź Ollamy miała kształt:

```json
{
  "message": {
    "content": "<czysty JSON zgodny z CvLlmDto, jako string>"
  }
}
```

— `content` był parsowany przez `CvLlmDto.model_validate_json(content)`.

**Obsługa błędów:**

- `httpx.HTTPError` (sieć/HTTP/timeout) → retry z exponential backoff, do `OLLAMA_MAX_RETRIES` prób; po wyczerpaniu prób → `RuntimeError`.
- Błąd walidacji Pydantic odpowiedzi (JSON niezgodny ze schematem) → **brak retry**, natychmiastowy `ValueError`.
- Oba wyjątki były łapane wyżej, w `CVPipelineOrchestrator.process_cv`, i tylko logowane jako ostrzeżenie — pipeline kontynuował z samym wynikiem heurystyki (`llm_result = None`).

## System prompt

```text
Ekstrahujesz dane z CV do JSON wg narzuconego schematu. Zachowaj oryginalny język; brak danych = null/[].
- work_experience: wpis per stanowisko; skills_used = technologie użyte konkretnie w tym okresie.
- certifications: tylko formalne certyfikaty/dyplomy/egzaminy (Docker, REST itp. to NIE certyfikaty).
- education.field_of_study: tylko kierunek studiów, nigdy technologie/projekty.
- languages: języki obce + poziom (np. angielski B2).
```

## Prompt użytkownika (`build_cv_extraction_prompt`)

Budowany dynamicznie z trzech części:

1. Nagłówek z instrukcją ("Przeanalizuj poniższy tekst CV i wyciągnij ustrukturyzowane informacje...").
2. **Podpowiedzi z heurystyki** (opcjonalnie, jeśli `heuristic_dates`/`heuristic_job_titles` niepuste) — wykryte zakresy dat i tytuły stanowisk, z instrukcją dla modelu, żeby zweryfikował/uzupełnił `work_experience` tak, by każdy wykryty zakres miał odpowiadający wpis.
3. Surowy tekst CV (`normalized_text`), otagowany `--- SUROWY TEKST CV --- ... --- KONIEC TEKSTU ---`.

Przykład wygenerowanego promptu (fragment):

```text
Przeanalizuj poniższy tekst CV i wyciągnij ustrukturyzowane informacje. Pamiętaj o wypełnieniu 'work_experience' dla każdego stanowiska.

--- PODPOWIEDZI Z WSTĘPNEJ ANALIZY (do weryfikacji, mogą być niepełne) ---
Poniższe zakresy dat i stanowiska zostały wykryte automatycznie w tekście. Upewnij się, że KAŻDY z nich ma odpowiadający wpis w 'work_experience' (możesz je poprawić lub uzupełnić, jeśli tekst mówi co innego):
Wykryte stanowiska: Senior Backend Developer, Fullstack Developer
Zakres dat: 2021-01-01 - obecnie
Zakres dat: 2018-03-01 - 2020-12-01
--- KONIEC PODPOWIEDZI ---

--- SUROWY TEKST CV ---
<tutaj normalized_text>
--- KONIEC TEKSTU ---
```

## Schemat `CvLlmDto` (ostatnia wersja przed usunięciem)

```python
class PersonalInfoDto(BaseModel):
    full_name: str | None
    email: str | None
    phone: str | None
    location: str | None
    linkedin_url: str | None

class ProjectDto(BaseModel):
    name: str
    description: str | None
    technologies: list[str]

class CvLlmDto(BaseModel):
    personal_info: PersonalInfoDto
    summary: str | None
    soft_skills: list[str]
    work_experience: list[WorkExperienceDto]   # zachowane w cv_llm.py
    projects: list[ProjectDto]
    education: list[EducationDto]              # zachowane w cv_llm.py
    languages: list[LanguageDto]                # zachowane w cv_llm.py
    certifications: list[str]
```

Pole `hard_skills: list[str]` istniało wcześniej na `CvLlmDto`, ale zostało usunięte jeszcze przed tą archiwizacją — hard skille i tak docelowo szły przez `TechStackValidator` (walidacja względem słownika), nie bezpośrednio z odpowiedzi LLM.

## Jak odtworzyć integrację, jeśli będzie potrzebna

1. Przywrócić `app/services/cv_pipeline/transform/llm/client.py` i `prompts.py` (treść wyżej) oraz `CvLlmDto`/`PersonalInfoDto`/`ProjectDto` w `app/schema/cv_llm.py`.
2. Przywrócić `OLLAMA_*` w `app/core/config.py` (wartości wyżej) i `OLLAMA_BASE_URL` + `extra_hosts` w `docker-compose.yml` (serwis `api`).
3. W `CVPipelineOrchestrator.process_cv` (`transform/pipeline.py`) dodać z powrotem wywołanie `OllamaLLMClient.parse_cv(...)` w `try/except`, tak by błąd Ollamy nie przerywał pipeline'u.
4. W `merge.py` `build_unified_record` dodać z powrotem parametr `llm_result: CvLlmDto | None` i logikę "LLM preferowany, heurystyka jako fallback" — ten branching został usunięty przy archiwizacji, trzeba go odtworzyć ręcznie (nie jest to proste `git revert`, bo pliki zmieniały się po drodze).
