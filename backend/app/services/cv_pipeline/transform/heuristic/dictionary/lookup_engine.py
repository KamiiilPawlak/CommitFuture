from flashtext import KeywordProcessor


class FlashLookupEngine:
    def __init__(self, keywords_map: dict[str, list[str]]):
        self.processor: KeywordProcessor = KeywordProcessor(case_sensitive=False)

        # UWAGA: "." nie jest tu dodawane. Traktowanie kropki jako znaku
        # "słowotwórczego" psuje dopasowania na końcu zdania/linii (częste w
        # CV, np. "...używałem Docker." nie łapało "Docker", bo trailing "."
        # zlepiał się ze słowem w jeden token różny od klucza "docker").
        # Keywordy zawierające kropkę ("Node.js", ".NET") działają bez tego
        # wpisu - flashtext dopasowuje je po samej treści klucza w trie.
        extra_chars: list[str] = ["+", "#", "-", *list("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")]
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

    def extract_matches_with_offsets(self, text: str) -> list[tuple[str, int]]:
        """Jak extract_matches, ale zwraca też offset startu każdego dopasowania w
        tekście — potrzebne do przypisywania technologii do najbliższego
        wcześniejszego wpisu doświadczenia (zakresu dat)."""
        if not text or not text.strip():
            return []

        spans: list[tuple[str, int, int]] = self.processor.extract_keywords(
            text, span_info=True
        )
        return [(canonical_name, start) for canonical_name, start, _end in spans]
