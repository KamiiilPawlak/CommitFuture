import regex as re

from .lookup_engine import FlashLookupEngine

LANGUAGES_DICTIONARY: dict[str, list[str]] = {
    "polski": ["polski", "polish"],
    "angielski": ["angielski", "english"],
    "niemiecki": ["niemiecki", "german", "deutsch"],
    "francuski": ["francuski", "french", "français"],
    "hiszpański": ["hiszpański", "hiszpanski", "spanish", "español"],
    "włoski": ["włoski", "wloski", "italian", "italiano"],
    "rosyjski": ["rosyjski", "russian"],
    "ukraiński": ["ukraiński", "ukrainski", "ukrainian"],
    "portugalski": ["portugalski", "portuguese"],
    "chiński": ["chiński", "chinski", "chinese", "mandarin"],
    "japoński": ["japoński", "japonski", "japanese"],
    "koreański": ["koreański", "koreanski", "korean"],
    "arabski": ["arabski", "arabic"],
    "holenderski": ["holenderski", "dutch"],
    "szwedzki": ["szwedzki", "swedish"],
    "norweski": ["norweski", "norwegian"],
    "czeski": ["czeski", "czech"],
    "słowacki": ["słowacki", "slowacki", "slovak"],
}

# Poziom biegłości szukany w krótkim oknie tekstu PO nazwie języka, np.
# "angielski B2", "english - fluent", "niemiecki: podstawowy".
_LEVEL_PATTERN = re.compile(
    r"(?i)\b(A1|A2|B1|B2|C1|C2"
    r"|native|ojczysty"
    r"|fluent|biegły|biegly"
    r"|advanced|bardzo dobry"
    r"|intermediate|komunikatywny|dobry"
    r"|basic|podstawowy)\b"
)

_LEVEL_SEARCH_WINDOW = 25

_languages_engine = FlashLookupEngine(LANGUAGES_DICTIONARY)


def extract_languages(text: str) -> list[dict[str, str | None]]:
    if not text or not text.strip():
        return []

    matches_with_offsets = _languages_engine.extract_matches_with_offsets(text)

    results: dict[str, str | None] = {}
    for language, offset in matches_with_offsets:
        window_start = offset
        window_end = min(len(text), offset + len(language) + _LEVEL_SEARCH_WINDOW)
        window = text[window_start:window_end]

        level_match = _LEVEL_PATTERN.search(window)
        level = level_match.group(0).upper() if level_match else None

        if language not in results or (results[language] is None and level):
            results[language] = level

    return [
        {"language": language, "level": level}
        for language, level in sorted(results.items())
    ]
