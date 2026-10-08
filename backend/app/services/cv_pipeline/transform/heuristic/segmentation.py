import regex as re

# Frazy nagłówków sekcji (PL/EN). Nagłówek to cała linia - albo "goła"
# (np. "Doświadczenie" / "EXPERIENCE" jako jedyna treść linii), albo z
# dwukropkiem i treścią w tej samej linii (np. "Certyfikaty: AWS, CKA").
# Fraza w środku zdania opisowego (np. "Doświadczenie w pracy z Pythonem")
# nie jest traktowana jako nagłówek, bo nie zaczyna linii / nie ma po sobie
# dwukropka.
SECTION_HEADER_PATTERNS: dict[str, str] = {
    "experience": (
        r"doświadczenie\s+zawodowe|doświadczenie|"
        r"historia\s+zatrudnienia|employment\s+history|"
        r"work\s+experience|professional\s+experience|experience"
    ),
    "education": r"wykształcenie|edukacja|education",
    "certifications": (
        r"certyfikaty|certyfikacje|licencje|kursy\s+i\s+certyfikaty|"
        r"certifications?|licenses?"
    ),
    "languages": r"języki(?:\s+obce)?|znajomość\s+języków|languages?",
    "skills": (
        r"umiejętności(?:\s+techniczne)?|kompetencje|stos\s+technologiczny|"
        r"skills?|tech\s+stack"
    ),
    "projects": r"projekty|projects?",
    "summary": r"podsumowanie|profil\s+zawodowy|o\s+mnie|summary|profile|about\s+me",
}

JOB_POSTING_SECTION_HEADER_PATTERNS: dict[str, str] = {
    "responsibilities": (
        r"(?:your\s+|key\s+)?responsibilities|what\s+you(?:'ll|\s+will)\s+do|"
        r"obowiązki|zakres\s+obowiązków|twoje\s+obowiązki"
    ),
    "requirements": (
        r"requirements|qualifications|what\s+we(?:'re|\s+are)\s+looking\s+for|"
        r"must\s+have|wymagania|wymagania\s+formalne|czego\s+oczekujemy"
    ),
    "nice_to_have": (
        r"nice\s+to\s+have|preferred(?:\s+qualifications)?|bonus(?:\s+points)?|"
        r"mile\s+widziane|dodatkowo|będzie\s+plusem|plusem\s+będzie"
    ),
}


def _build_header_patterns(
    header_patterns: dict[str, str],
) -> tuple[dict[str, re.Pattern[str]], dict[str, re.Pattern[str]]]:
    bare = {
        key: re.compile(rf"^(?:{pattern})\s*:?$", re.IGNORECASE)
        for key, pattern in header_patterns.items()
    }
    inline = {
        key: re.compile(rf"^(?:{pattern})\s*:\s*", re.IGNORECASE)
        for key, pattern in header_patterns.items()
    }
    return bare, inline


_BARE_HEADER_PATTERNS, _INLINE_HEADER_PATTERNS = _build_header_patterns(
    SECTION_HEADER_PATTERNS
)


def _match_header(
    line: str,
    bare_patterns: dict[str, re.Pattern[str]],
    inline_patterns: dict[str, re.Pattern[str]],
) -> tuple[str, int] | None:
    """Sprawdza, czy linia jest nagłówkiem sekcji. Zwraca (typ_sekcji,
    offset_treści_w_tej_linii) albo None."""
    stripped = line.strip()
    if not stripped:
        return None

    leading_ws = len(line) - len(line.lstrip())

    for section_type, bare_pattern in bare_patterns.items():
        if bare_pattern.fullmatch(stripped):
            return section_type, len(line)

    for section_type, inline_pattern in inline_patterns.items():
        inline_match = inline_pattern.match(stripped)
        if inline_match and len(stripped) > inline_match.end():
            return section_type, leading_ws + inline_match.end()

    return None


def find_sections(
    text: str, header_patterns: dict[str, str] | None = None
) -> list[tuple[str, int, int]]:
    """Dzieli tekst (CV albo ogłoszenie o pracę) na sekcje na podstawie
    nagłówków. Domyślnie używa SECTION_HEADER_PATTERNS (sekcje CV) - dla
    ogłoszeń o pracę przekaż JOB_POSTING_SECTION_HEADER_PATTERNS. Zwraca
    listę (typ_sekcji, start, end), gdzie start/end to offsety treści
    NALEŻĄCEJ do sekcji (bez samej frazy nagłówka). Tekst przed pierwszym
    nagłówkiem nie trafia do żadnej sekcji.
    """
    if not text:
        return []

    bare_patterns, inline_patterns = (
        (_BARE_HEADER_PATTERNS, _INLINE_HEADER_PATTERNS)
        if header_patterns is None
        else _build_header_patterns(header_patterns)
    )

    headers: list[tuple[str, int]] = []
    offset = 0
    for line in text.split("\n"):
        matched = _match_header(line, bare_patterns, inline_patterns)
        if matched is not None:
            section_type, content_offset_in_line = matched
            headers.append((section_type, offset + content_offset_in_line))
        offset += len(line) + 1

    if not headers:
        return []

    sections: list[tuple[str, int, int]] = []
    for i, (section_type, content_start) in enumerate(headers):
        content_end = headers[i + 1][1] if i + 1 < len(headers) else len(text)
        sections.append((section_type, content_start, content_end))

    return sections


def spans_for_type(
    sections: list[tuple[str, int, int]], section_type: str
) -> list[tuple[int, int]]:
    return [(start, end) for stype, start, end in sections if stype == section_type]


def offset_in_spans(offset: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= offset < end for start, end in spans)
