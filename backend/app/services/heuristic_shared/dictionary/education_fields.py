import regex as re

from .lookup_engine import FlashLookupEngine

# Kanoniczna kategoria kierunku studiów -> warianty zapisu (PL/EN). Celowo
# nie zawiera nazw technologii/projektów - 'kierunek' to pole studiów, nie
# stos technologiczny (ten rozdział jest też pilnowany przez prompt LLM,
# a teraz odtwarzamy go bez LLM).
EDUCATION_FIELDS_DICTIONARY: dict[str, list[str]] = {
    "Computer Science": [
        "computer science",
        "informatyka",
        "informatyka i ekonometria",
    ],
    "Software Engineering": [
        "software engineering",
        "inżynieria oprogramowania",
        "inzynieria oprogramowania",
    ],
    "Information Technology": [
        "information technology",
        "technologie informacyjne",
        "technologia informacyjna",
    ],
    "Electrical Engineering": [
        "electrical engineering",
        "elektrotechnika",
    ],
    "Electronics and Telecommunications": [
        "electronics and telecommunications",
        "elektronika i telekomunikacja",
    ],
    "Automation and Robotics": [
        "automation and robotics",
        "automatyka i robotyka",
    ],
    "Mechanical Engineering": [
        "mechanical engineering",
        "mechanika",
        "budowa maszyn",
    ],
    "Mathematics": [
        "mathematics",
        "matematyka",
    ],
    "Data Science": [
        "data science",
        "analiza danych",
    ],
    "Physics": [
        "physics",
        "fizyka",
    ],
    "Management": [
        "management",
        "zarządzanie",
        "zarzadzanie",
    ],
    "Economics": [
        "economics",
        "ekonomia",
    ],
    "Business Administration": [
        "business administration",
        "zarządzanie i inżynieria produkcji",
    ],
    "Biotechnology": [
        "biotechnology",
        "biotechnologia",
    ],
    "Chemistry": [
        "chemistry",
        "chemia",
    ],
}

_FIELD_ANCHOR_PATTERN = re.compile(
    r"(?i)(kierunek|specjalizacja|studia\s+na|field\s+of\s+study|major\s+in)\s*[:\-]?\s*"
)

_education_fields_engine = FlashLookupEngine(EDUCATION_FIELDS_DICTIONARY)


def extract_field_of_study(text: str) -> str | None:
    """Zwraca znormalizowaną kategorię kierunku studiów. Preferuje dopasowanie
    znajdujące się blisko po słowach-kotwicach ('kierunek', 'field of
    study'...), bo w CV ten sam tekst może zawierać wiele kategorii (np. w
    opisie doświadczenia), a interesuje nas tylko ta w sekcji edukacji."""
    if not text or not text.strip():
        return None

    matches_with_offsets = _education_fields_engine.extract_matches_with_offsets(text)
    if not matches_with_offsets:
        return None

    anchor_offsets = [m.end() for m in _FIELD_ANCHOR_PATTERN.finditer(text)]

    for field, offset in sorted(matches_with_offsets, key=lambda m: m[1]):
        for anchor_offset in anchor_offsets:
            if 0 <= offset - anchor_offset <= 40:
                return field

    return matches_with_offsets[0][0]


def extract_field_of_study_categories(text: str) -> list[str]:
    """Zwraca WSZYSTKIE znormalizowane kategorie kierunków znalezione w
    tekście - w przeciwieństwie do extract_field_of_study (jedna najbardziej
    prawdopodobna kategoria z CV) tu wejściem jest zwykle ogłoszenie o pracę,
    które wylicza kilka akceptowanych kierunków naraz (np. 'Degree in
    Computer Science, Software Engineering, Engineering or a related
    field')."""
    if not text or not text.strip():
        return []

    return _education_fields_engine.extract_matches(text)


def normalize_field_of_study(field_of_study_text: str | None) -> str | None:
    """Mapuje już wyizolowany, krótki kierunek studiów (np.
    EducationDto.field_of_study - niezależnie czy pochodzi z LLM, czy z
    extract_field_of_study) na znormalizowaną kategorię. W przeciwieństwie do
    extract_field_of_study nie szuka słów-kotwic w długim tekście CV - tu
    wejściem jest już sam kierunek, np. 'Informatyka' albo 'Computer
    Science'."""
    if not field_of_study_text or not field_of_study_text.strip():
        return None

    matches = _education_fields_engine.extract_matches(field_of_study_text)
    return matches[0] if matches else None
