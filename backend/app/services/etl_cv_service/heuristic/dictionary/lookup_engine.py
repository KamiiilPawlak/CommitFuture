from flashtext import KeywordProcessor  # type: ignore[import-untyped]


class FlashLookupEngine:
    def __init__(self, keywords_map: dict[str, list[str]]):
        self.processor: KeywordProcessor = KeywordProcessor(case_sensitive=False)

        extra_chars: list[str] = ["+", "#", ".", "-", *list("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")]
        for char in extra_chars:
            self.processor.add_non_word_boundary(char)

        self._build_keywords(keywords_map)

    def _build_keywords(self, keywords_map: dict[str, list[str]]) -> None:
        canonical_name: str
        aliases: list[str]
        for canonical_name, aliases in keywords_map.items():
            for alias in aliases:
                self.processor.add_keyword(alias, canonical_name)

    def extract_matches(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        matches: list[str] = self.processor.extract_keywords(text)
        return sorted(set(matches))
