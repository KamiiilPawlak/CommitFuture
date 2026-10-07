from __future__ import annotations

from datetime import date

from app.schema.cv_llm import WorkExperienceDto
from app.services.etl_cv_service.heuristic.domain.experience_calc import (
    convert_extracted_range_to_dates,
    merge_overlapping_ranges,
)
from app.services.etl_cv_service.heuristic.domain.models import DateRange

_CURRENT_MARKERS = {"present", "obecnie", "aktualnie", "now"}

_DAYS_PER_MONTH = 30.4375


def _parse_role_date(value: str | None) -> date | None:
    """Parsuje datę w formacie zwracanym przez LLM dla WorkExperienceDto (YYYY-MM lub YYYY)."""
    if not value:
        return None

    cleaned = value.strip()

    if len(cleaned) == 4 and cleaned.isdigit():
        return date(int(cleaned), 1, 1)

    if len(cleaned) == 7 and cleaned[4] == "-":
        year_str, month_str = cleaned.split("-")
        if year_str.isdigit() and month_str.isdigit():
            return date(int(year_str), int(month_str), 1)

    return None


def _is_current_role(end_date: str | None) -> bool:
    """Reguła z Punktu 3: rola jest aktualna, jeśli brak end_date lub jest to marker typu 'present'/'obecnie'."""
    if not end_date:
        return True
    return end_date.strip().lower() in _CURRENT_MARKERS


def _role_date_span(entry: WorkExperienceDto) -> tuple[date, date] | None:
    start = _parse_role_date(entry.start_date)
    if start is None:
        return None

    is_current = _is_current_role(entry.end_date)
    end = None if is_current else _parse_role_date(entry.end_date)

    return convert_extracted_range_to_dates(
        DateRange(start_date=start, end_date=end, is_current=is_current)
    )


def compute_skill_usage(
    work_experience: list[WorkExperienceDto],
) -> dict[str, dict[str, int | str | None]]:
    """Punkt 1: liczy months_used/last_used per skill na podstawie dat z work_experience.

    Celowo NIE prosi LLM o tę arytmetykę (zawodny w przecinaniu dat z wielu ról) —
    ta sama logika co ExperienceService.calculate_experience, tylko per-skill.
    """
    skill_spans: dict[str, list[tuple[date, date]]] = {}
    skill_is_current: dict[str, bool] = {}

    for entry in work_experience:
        span = _role_date_span(entry)
        if span is None:
            continue

        is_current = _is_current_role(entry.end_date)

        for raw_skill in entry.skills_used:
            skill = raw_skill.strip()
            if not skill:
                continue

            skill_spans.setdefault(skill, []).append(span)
            if is_current:
                skill_is_current[skill] = True

    result: dict[str, dict[str, int | str | None]] = {}
    for skill, spans in skill_spans.items():
        merged = merge_overlapping_ranges(spans)
        total_days = sum((end - start).days + 1 for start, end in merged)
        months_used = round(total_days / _DAYS_PER_MONTH)

        if skill_is_current.get(skill):
            last_used = str(date.today().year)
        else:
            last_used = str(max(end for _, end in merged).year)

        result[skill] = {"months_used": months_used, "last_used": last_used}

    return result
