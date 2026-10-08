from __future__ import annotations

from datetime import date
from typing import Any, Final, Literal

from app.schema.cv_llm import CvLlmDto, WorkExperienceDto
from app.services.cv_pipeline.transform.dictionaries.validator import TechStackValidator
from app.services.cv_pipeline.transform.heuristic.domain.experience_calc import (
    convert_extracted_range_to_dates,
    merge_overlapping_ranges,
)
from app.services.cv_pipeline.transform.heuristic.domain.models import DateRange

_CURRENT_MARKERS: Final[set[str]] = {"present", "obecnie", "aktualnie", "now"}

_DAYS_PER_MONTH: Final[float] = 30.4375

_YEAR_ONLY_LENGTH: Final[int] = 4
_YEAR_MONTH_LENGTH: Final[int] = 7

_SENIORITY_THRESHOLDS: Final[list[tuple[int, str]]] = [
    (24, "junior"),
    (72, "mid"),
]
_SENIORITY_DEFAULT: Final[str] = "senior"

FieldSource: Final[Literal["heuristic", "llm", "merged"]] = Literal[
    "heuristic", "llm", "merged"
]


def _parse_role_date(value: str | None) -> date | None:
    if not value:
        return None

    cleaned: str = value.strip()

    if len(cleaned) == _YEAR_ONLY_LENGTH and cleaned.isdigit():
        return date(int(cleaned), 1, 1)

    if len(cleaned) == _YEAR_MONTH_LENGTH and cleaned[_YEAR_ONLY_LENGTH] == "-":
        year_str: str
        month_str: str
        year_str, month_str = cleaned.split("-")
        if year_str.isdigit() and month_str.isdigit():
            return date(int(year_str), int(month_str), 1)

    return None


def is_current_role(end_date: str | None) -> bool:
    if not end_date:
        return True
    return end_date.strip().lower() in _CURRENT_MARKERS


def _role_date_span(entry: WorkExperienceDto) -> tuple[date, date] | None:
    start: date | None = _parse_role_date(entry.start_date)
    if start is None:
        return None

    is_current: bool = is_current_role(entry.end_date)
    end: date | None = None if is_current else _parse_role_date(entry.end_date)

    return convert_extracted_range_to_dates(
        DateRange(start_date=start, end_date=end, is_current=is_current)
    )


def compute_skill_usage(
    work_experience: list[WorkExperienceDto],
    validator: TechStackValidator,
) -> dict[str, dict[str, int | str | None]]:
    skill_spans: dict[str, list[tuple[date, date]]] = {}
    skill_is_current: dict[str, bool] = {}

    for entry in work_experience:
        span: tuple[date, date] | None = _role_date_span(entry)
        if span is None:
            continue

        is_current: bool = is_current_role(entry.end_date)

        for skill in validator.validate_skills(entry.skills_used):
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


def build_work_experience_entry(
    entry: WorkExperienceDto, validator: TechStackValidator
) -> dict[str, object]:
    return {
        "company": entry.company,
        "role": entry.role,
        "start_date": entry.start_date,
        "end_date": None if is_current_role(entry.end_date) else entry.end_date,
        "is_current": is_current_role(entry.end_date),
        "responsibilities": entry.responsibilities,
        "skills_used": validator.validate_skills(entry.skills_used),
    }


def estimate_seniority(total_experience_months: int) -> str:
    for threshold_months, label in _SENIORITY_THRESHOLDS:
        if total_experience_months < threshold_months:
            return label
    return _SENIORITY_DEFAULT


def resolve_field(
    heuristic_value: str | None,
    llm_value: str | None,
    *,
    prefer: Literal["heuristic", "llm"],
) -> tuple[str | None, FieldSource]:
    if heuristic_value and llm_value:
        if heuristic_value.strip().lower() == llm_value.strip().lower():
            return heuristic_value, "merged"
        return (
            (heuristic_value, "heuristic")
            if prefer == "heuristic"
            else (llm_value, "llm")
        )
    if heuristic_value:
        return heuristic_value, "heuristic"
    if llm_value:
        return llm_value, "llm"
    return None, "merged"


def build_flat_tech_stack(
    hard_skills: list[str],
    heuristic_tech_stack: list[str],
    validator: TechStackValidator,
) -> list[str]:
    return validator.validate_skills([*hard_skills, *heuristic_tech_stack])


def build_hard_skills(
    work_experience: list[WorkExperienceDto],
    llm_hard_skills: list[str],
    heuristic_tech_stack: list[str],
    validator: TechStackValidator,
) -> list[dict[str, Any]]:
    usage = compute_skill_usage(work_experience, validator)
    llm_set = set(validator.validate_skills(llm_hard_skills))
    heuristic_set = set(validator.validate_skills(heuristic_tech_stack))

    all_skills: set[str] = set(usage) | llm_set | heuristic_set

    result: list[dict[str, Any]] = []
    for skill in sorted(all_skills):
        in_llm: bool = skill in llm_set
        in_heuristic: bool = skill in heuristic_set

        source: FieldSource
        if in_llm and in_heuristic:
            source = "merged"
        elif in_llm:
            source = "llm"
        else:
            source = "heuristic"

        skill_usage: dict[str, Any] = usage.get(skill, {})
        result.append(
            {
                "name": skill,
                "months_used": skill_usage.get("months_used"),
                "last_used": skill_usage.get("last_used"),
                "source": source,
            }
        )

    return result


def build_unified_record(
    heuristic_result: dict[str, Any],
    llm_result: CvLlmDto | None,
    llm_warnings: list[str],
    validated_hard_skills: list[str],
    validator: TechStackValidator,
) -> dict[str, Any]:
    heuristic_phones: list[str] = heuristic_result.get("phones", [])
    heuristic_phone: str | None = heuristic_phones[0] if heuristic_phones else None

    email, email_source = resolve_field(
        heuristic_result.get("email"),
        llm_result.personal_info.email if llm_result else None,
        prefer="heuristic",
    )
    phone, phone_source = resolve_field(
        heuristic_phone,
        llm_result.personal_info.phone if llm_result else None,
        prefer="heuristic",
    )

    work_experience = llm_result.work_experience if llm_result else []
    total_experience_months: int = heuristic_result.get("total_experience_months", 0)

    return {
        "personal_info": {
            "full_name": llm_result.personal_info.full_name if llm_result else None,
            "email": email,
            "phone": phone,
            "location": llm_result.personal_info.location if llm_result else None,
            "linkedin_url": llm_result.personal_info.linkedin_url
            if llm_result
            else None,
        },
        "summary": llm_result.summary if llm_result else None,
        "total_experience_months": total_experience_months,
        "seniority_estimate": estimate_seniority(total_experience_months),
        "work_experience": [
            build_work_experience_entry(entry, validator) for entry in work_experience
        ],
        "skills": {
            "hard": build_hard_skills(
                work_experience,
                validated_hard_skills,
                heuristic_result.get("tech_stack", []),
                validator,
            ),
            "soft": llm_result.soft_skills if llm_result else [],
            "all_tech_stack_flat": build_flat_tech_stack(
                validated_hard_skills, heuristic_result.get("tech_stack", []), validator
            ),
        },
        "education": [e.model_dump() for e in llm_result.education]
        if llm_result
        else [],
        "languages": [lang.model_dump() for lang in llm_result.languages]
        if llm_result
        else [],
        "certifications": llm_result.certifications if llm_result else [],
        "validation": {
            "warnings": llm_warnings,
            "field_confidence": {
                "email": email_source,
                "phone": phone_source,
            },
        },
    }
