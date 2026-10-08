from datetime import date
from typing import cast

import dateparser
import regex as re


def _parse_single_date(date_str: str) -> date | str | None:
    cleaned = date_str.strip().lower()

    if re.match(r"^(obecnie|present|now|aktualnie)$", cleaned):
        return "present"

    if re.fullmatch(r"\d{4}", cleaned):
        return date(int(cleaned), 1, 1)

    # Format kanoniczny "YYYY-MM" produkowany przez CVTextNormalizer._normalize_dates.
    match_ym = re.fullmatch(r"(\d{4})-(\d{1,2})", cleaned)
    if match_ym:
        year, month = map(int, match_ym.groups())
        return date(year, month, 1)

    match_my = re.fullmatch(r"(\d{1,2})[\./](\d{4})", cleaned)
    if match_my:
        month, year = map(int, match_my.groups())
        return date(year, month, 1)

    settings = {
        "PREFER_DAY_OF_MONTH": "first",
        "PREFER_DATES_FROM": "past",
        "DATE_ORDER": "DMY",
        "REQUIRE_PARTS": ["year"],
    }

    parsed = dateparser.parse(date_str, settings=settings)
    if parsed is not None:
        return parsed.date()

    return None


_DATE_COMPONENT_PATTERN = (
    # Jeden człon daty w jednym z obsługiwanych formatów - uporządkowane od
    # najbardziej do najmniej specyficznego, tak aby np. "2020-03" nie było
    # dopasowane tylko jako samo "2020":
    #   DD.MM.YYYY | YYYY-MM (format kanoniczny z CVTextNormalizer) | MM.YYYY | YYYY
    r"(?:\d{1,2}[\./]\d{1,2}[\./]\d{4}"
    r"|\d{4}-\d{1,2}"
    r"|\d{1,2}[\./]\d{4}"
    r"|\d{4})"
)

_DATE_RANGE_PATTERN = re.compile(
    rf"({_DATE_COMPONENT_PATTERN})\s*(?:-+|—|do|to)\s*"
    rf"({_DATE_COMPONENT_PATTERN}|obecnie|present|aktualnie|now)",
    re.IGNORECASE,
)


def _find_date_ranges(
    text: str,
) -> list[tuple[date, date | None, bool, int]]:
    results: list[tuple[date, date | None, bool, int]] = []

    for match in _DATE_RANGE_PATTERN.finditer(text):
        start_raw, end_raw = match.groups()

        start_date = _parse_single_date(start_raw)
        end_raw_parsed = _parse_single_date(end_raw)

        if isinstance(start_date, date):
            is_current = end_raw_parsed == "present"
            end_date = None if is_current else cast(date | None, end_raw_parsed)
            results.append((start_date, end_date, is_current, match.start()))

    return results


def extract_date_ranges(text: str) -> list[dict[str, date | bool | str | None]]:
    return [
        {"start_date": start_date, "end_date": end_date, "is_current": is_current}
        for start_date, end_date, is_current, _offset in _find_date_ranges(text)
    ]


def extract_date_ranges_with_offsets(
    text: str,
) -> list[dict[str, date | bool | str | int | None]]:
    """Jak extract_date_ranges, ale z dodatkowym kluczem 'offset' (pozycja
    początku dopasowania w tekście) — potrzebnym do przypisywania wpisów
    doświadczenia (tech stack, obowiązki) do najbliższego wcześniejszego
    zakresu dat bez pomocy LLM."""
    return [
        {
            "start_date": start_date,
            "end_date": end_date,
            "is_current": is_current,
            "offset": offset,
        }
        for start_date, end_date, is_current, offset in _find_date_ranges(text)
    ]
