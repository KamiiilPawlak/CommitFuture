import json
from pathlib import Path
from typing import Any

DICTIONARY_PATH = Path(__file__).parent / "tech_stack.json"


class TechStackValidator:
    def __init__(self, dict_path: Path = DICTIONARY_PATH) -> None:
        self.synonym_map: dict[str, str] = {}
        self.canonical_skills: set[str] = set()
        self._load_dictionary(dict_path)

    def _register_category(self, category_data: dict[str, list[str]]) -> None:
        """Helper do rejestrowania par kanoniczna_nazwa -> synonimy."""
        for canonical, synonyms in category_data.items():
            canonical_clean = canonical.lower()
            self.canonical_skills.add(canonical_clean)

            self.synonym_map[canonical_clean] = canonical_clean
            for synonym in synonyms:
                self.synonym_map[synonym.lower()] = canonical_clean

    def _load_dictionary(self, path: Path) -> None:
        if not path.exists():
            return

        with path.open(encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        for key, value in data.items():
            if isinstance(value, dict):
                self._register_category(value)
            elif isinstance(value, list):
                self._register_category({key: value})

    def normalize_skill(self, skill: str) -> str | None:
        clean_skill = skill.strip().lower()
        return self.synonym_map.get(clean_skill)

    def validate_skills(self, skills: list[str]) -> list[str]:
        normalized: set[str] = set()
        for skill in skills:
            canonical = self.normalize_skill(skill)
            if canonical:
                normalized.add(canonical)
        return sorted(normalized)
