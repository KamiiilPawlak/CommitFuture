SYSTEM_PROMPT = """Jesteś precyzyjnym systemem ETL do parsowania dokumentów CV.
Twoim zadaniem jest przeanalizowanie surowego tekstu CV i wyciągnięcie z niego ustrukturyzowanych danych dokładnie według podanego schematu JSON.

Zasady:
1. Zachowaj oryginalny język wpisów (nie tłumacz nazw projektów ani opisów stanowisk).
2. Jeśli dana informacja nie występuje w tekście, pozostaw pole jako `null` lub pusta lista `[]`.
3. Pole `hard_skills` jest KLUCZOWE: musisz wyciągnąć do niego WSZYSTKIE wymienione technologie, języki programowania, frameworki, bazy danych, narzędzia (np. Python, FastAPI, Docker, Git, SQL, React). Szukaj ich w sekcji umiejętności, w opisach doświadczenia i wszędzie w tekście.
4. Pole `work_experience` jest RÓWNIE KLUCZOWE: MUSI zawierać jeden obiekt na KAŻDE stanowisko/okres zatrudnienia wymienione w tekście, nawet jeśli jakieś pole (np. nazwa firmy) nie jest znane. Nie pomijaj żadnego stanowiska. Dla każdego stanowiska wypełnij `skills_used` — ale TYLKO technologiami faktycznie wymienionymi w opisie TEGO konkretnego stanowiska, nie całym `hard_skills` z CV.
5. Pole `certifications` NIE jest tym samym co `hard_skills`. Wpisuj tam WYŁĄCZNIE nazwy formalnych certyfikatów/egzaminów/kursów z dyplomem (np. "AWS Certified Solutions Architect", "CCNA", "Pytest Automation Certificate"). Nazwy technologii, protokołów, bibliotek czy standardów (np. GraphQL, Swagger, OpenAPI, Docker, REST) NIGDY nie trafiają do `certifications` — nawet jeśli brzmią formalnie, to są `hard_skills`.
6. W sekcji `education`, pole `field_of_study` MUSI zawierać WYŁĄCZNIE kierunek/specjalizację studiów (np. "Inżynieria Oprogramowania", "Informatyka"). NIGDY nie wpisuj tam nazwy projektu, pracy dyplomowej, przedmiotu czy technologii (np. "Async Task Manager" to nazwa projektu, nie kierunek studiów) — jeśli nie masz pewności co do kierunku, zostaw `null`.
7. Odpowiadaj WYŁĄCZNIE poprawnym obiektem JSON zgodnym ze schematem. Nie dodawaj wstępów ani komentarzy.
"""


def _format_heuristic_hints(
    heuristic_dates: list[dict[str, object]] | None,
    heuristic_job_titles: list[str] | None,
) -> str:
    if not heuristic_dates and not heuristic_job_titles:
        return ""

    lines = [
        "--- PODPOWIEDZI Z WSTĘPNEJ ANALIZY (do weryfikacji, mogą być niepełne) ---",
        "Poniższe zakresy dat i stanowiska zostały wykryte automatycznie w tekście. "
        "Upewnij się, że KAŻDY z nich ma odpowiadający wpis w 'work_experience' "
        "(możesz je poprawić lub uzupełnić, jeśli tekst mówi co innego):",
    ]

    if heuristic_job_titles:
        lines.append(f"Wykryte stanowiska: {', '.join(heuristic_job_titles)}")

    if heuristic_dates:
        for date_range in heuristic_dates:
            start = date_range.get("start_date")
            end = "obecnie" if date_range.get("is_current") else date_range.get("end_date")
            lines.append(f"Zakres dat: {start} - {end}")

    lines.append("--- KONIEC PODPOWIEDZI ---\n")
    return "\n".join(lines)


def build_cv_extraction_prompt(
    raw_text: str,
    heuristic_dates: list[dict[str, object]] | None = None,
    heuristic_job_titles: list[str] | None = None,
) -> str:
    hints = _format_heuristic_hints(heuristic_dates, heuristic_job_titles)

    return f"""Przeanalizuj poniższy tekst CV i wyciągnij ustrukturyzowane informacje. Pamiętaj o wypisaniu wszystkich umiejętności technicznych do tablicy 'hard_skills' oraz o wypełnieniu 'work_experience' dla każdego stanowiska.

{hints}--- SUROWY TEKST CV ---
{raw_text}
--- KONIEC TEKSTU ---
"""
