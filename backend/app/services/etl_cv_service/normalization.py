from dataclasses import dataclass, field
from datetime import datetime
from typing import cast

import dateparser
import regex  # type: ignore[import-untyped]
from loguru import logger


@dataclass(frozen=True)
class NormalizerPatterns:
    dashes: regex.Pattern = field(
        default_factory=lambda: regex.compile(
            r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]"
        )
    )
    quotes: regex.Pattern = field(default_factory=lambda: regex.compile(r"[„”\"«»]"))
    multiple_spaces: regex.Pattern = field(
        default_factory=lambda: regex.compile(r"[ \t]+")
    )

    text_date: regex.Pattern = field(
        default_factory=lambda: regex.compile(
            r"\b(stycz(?:eń|nia)|lut(?:y|ego)|marz(?:ec|a)|kwiet(?:eń|nia)|maj(?:a)?|czerw(?:iec|ca)|lip(?:iec|ca)|sierp(?:ień|nia)|wrzes(?:ień|nia)|październik(?:a)?|listopad(?:a)?|grudzi(?:eń|nia)|january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(20\d{2}|19\d{2})\b",
            regex.IGNORECASE,
        )
    )

    digits_date_month_first: regex.Pattern = field(
        default_factory=lambda: regex.compile(
            r"\b(0[1-9]|1[0-2])[\./](20\d{2}|19\d{2})\b"
        )
    )
    digits_date: regex.Pattern = digits_date_month_first
    digits_date_year_first: regex.Pattern = field(
        default_factory=lambda: regex.compile(
            r"\b(20\d{2}|19\d{2})[\./](0[1-9]|1[0-2])\b"
        )
    )

    present: regex.Pattern = field(
        default_factory=lambda: regex.compile(
            r"\b(obecnie|teraz|aktualnie|present|w tej chwili|do dziś|do teraz)\b",
            regex.IGNORECASE,
        )
    )

    lang: regex.Pattern = field(
        default_factory=lambda: regex.compile(
            r"\b([a-cA-C])[-\s]*([1-2])\b", regex.IGNORECASE
        )
    )
    phone: regex.Pattern = field(
        default_factory=lambda: regex.compile(
            r"(?:\+\d{1,3}[ \t\-]*)?\(?\d{3}\)?[ \t\-]*\d{3}[ \t\-]*\d{3,4}\b"
        )
    )
    phone_clean: regex.Pattern = field(
        default_factory=lambda: regex.compile(r"[\s\-\(\)]")
    )

    url_prefix: regex.Pattern = field(
        default_factory=lambda: regex.compile(
            r"https?://(?:www\.)?(github\.com|linkedin\.com(?:\/in)?|linkedin\.pl)/?",
            regex.IGNORECASE,
        )
    )


class CVTextNormalizer:
    def __init__(self, patterns: NormalizerPatterns = NormalizerPatterns()) -> None:
        self._patterns = patterns

    def normalize_text(self, text: str) -> str:
        if not text:
            return ""

        logger.debug("[ETL - NORMALIZER] Uruchomienie etapów transformacji.")
        text = self._normalize_punctuation(text)
        text = self._normalize_dates(text)
        text = self._normalize_phone_numbers(text)
        text = self._normalize_hyperlinks(text)
        text = self._normalize_language_levels(text)
        return self._patterns.multiple_spaces.sub(" ", text)

    def _normalize_punctuation(self, text: str) -> str:
        text = self._patterns.dashes.sub("-", text)
        return self._patterns.quotes.sub('"', text)

    def _normalize_language_levels(self, text: str) -> str:
        return str(
            self._patterns.lang.sub(lambda m: f"{m.group(1).upper()}{m.group(2)}", text)
        )

    def _normalize_phone_numbers(self, text: str) -> str:
        def clean_phone(match: regex.Match) -> str:
            return str(self._patterns.phone_clean.sub("", match.group(0)))

        return cast(str, self._patterns.phone.sub(clean_phone, text))

    def _normalize_hyperlinks(self, text: str) -> str:
        return cast(str, self._patterns.url_prefix.sub(r"\1/", text))

    def _normalize_dates(self, text: str) -> str:
        text = self._patterns.digits_date.sub(r"\2-\1", text)
        text = self._patterns.digits_date_year_first.sub(r"\1-\2", text)

        def replace_with_dateparser(match: regex.Match) -> str:
            full_match = match.group(0)
            year = match.group(2)

            parsed_date = dateparser.parse(
                full_match,
                languages=["pl", "en"],
                settings={"PREFER_DAY_OF_MONTH": "first"},
            )
            if isinstance(parsed_date, datetime):
                return parsed_date.strftime("%Y-%m")
            return f"{year}-01"

        text = self._patterns.text_date.sub(replace_with_dateparser, text)
        return cast(str, self._patterns.present.sub("PRESENT", text))
