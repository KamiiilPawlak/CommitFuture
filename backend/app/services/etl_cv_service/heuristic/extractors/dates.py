from datetime import date
from typing import cast

import dateparser
import regex as re  # type: ignore[import-untyped]


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


def extract_date_ranges(text: str) -> list[dict[str, date | bool | str | None]]:
    # Jeden człon daty w jednym z obsługiwanych formatów - uporządkowane od
    # najbardziej do najmniej specyficznego, tak aby np. "2020-03" nie było
    # dopasowane tylko jako samo "2020":
    #   DD.MM.YYYY | YYYY-MM (format kanoniczny z CVTextNormalizer) | MM.YYYY | YYYY
    date_component_pattern = (
        r"(?:\d{1,2}[\./]\d{1,2}[\./]\d{4}"
        r"|\d{4}-\d{1,2}"
        r"|\d{1,2}[\./]\d{4}"
        r"|\d{4})"
    )

    date_range_pattern = re.compile(
        rf"({date_component_pattern})\s*(?:-+|—|do|to)\s*"
        rf"({date_component_pattern}|obecnie|present|aktualnie|now)",
        re.IGNORECASE,
    )

    results: list[dict[str, date | bool | str | None]] = []

    for match in date_range_pattern.finditer(text):
        start_raw, end_raw = match.groups()

        start_date = _parse_single_date(start_raw)
        end_raw_parsed = _parse_single_date(end_raw)

        if isinstance(start_date, date):
            is_current = end_raw_parsed == "present"
            end_date = None if is_current else cast(date | None, end_raw_parsed)

            results.append(
                {
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_current": is_current,
                }
            )

    return results
