from __future__ import annotations

from datetime import date
from typing import Any, Final, Literal

from app.schema.cv_extraction_dto import WorkExperienceDto
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

# Źródło pola jest dziś zawsze "heuristic" - bez LLM nie ma już z czym
# "mergować". Literal zostaje szerszy niż faktycznie produkowane wartości,
# żeby nie trzeba było jednocześnie zmieniać CVStructuredRecord/HardSkillRecord.
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


def build_flat_tech_stack(
    heuristic_tech_stack: list[str],
    validator: TechStackValidator,
) -> list[str]:
    return validator.validate_skills(heuristic_tech_stack)


def build_hard_skills(
    work_experience: list[WorkExperienceDto],
    heuristic_tech_stack: list[str],
    validator: TechStackValidator,
) -> list[dict[str, Any]]:
    usage = compute_skill_usage(work_experience, validator)
    heuristic_set = set(validator.validate_skills(heuristic_tech_stack))

    all_skills: set[str] = set(usage) | heuristic_set

    result: list[dict[str, Any]] = []
    for skill in sorted(all_skills):
        skill_usage: dict[str, Any] = usage.get(skill, {})
        result.append(
            {
                "name": skill,
                "months_used": skill_usage.get("months_used"),
                "last_used": skill_usage.get("last_used"),
                "source": "heuristic",
            }
        )

    return result


def _heuristic_candidate_to_work_experience_dto(
    candidate: dict[str, Any],
) -> WorkExperienceDto:
    """Zamienia wpis z HeuristicExtractionManager.work_experience_candidates
    (daty jako obiekty `date`, skille jako {"name","category"}) na
    WorkExperienceDto - wspólny kształt danych używany dalej przez
    compute_skill_usage/build_hard_skills/build_work_experience_entry. Brak
    company/responsibilities: heurystyka (słowniki + offsety) nie potrafi
    wyciągnąć wolnego tekstu bez NER/LLM."""
    start_date: date | None = candidate.get("start_date")
    end_date: date | None = candidate.get("end_date")

    return WorkExperienceDto(
        company=None,
        role=candidate.get("job_title"),
        start_date=start_date.strftime("%Y-%m") if start_date else None,
        end_date="Present"
        if candidate.get("is_current")
        else (end_date.strftime("%Y-%m") if end_date else None),
        responsibilities=[],
        skills_used=[skill["name"] for skill in candidate.get("skills_used", [])],
    )


def _build_education_from_heuristic(
    education_field_of_study: str | None,
) -> list[dict[str, Any]]:
    """Heurystyka wyciąga tylko znormalizowaną kategorię kierunku studiów,
    nie instytucję/tytuł/rok - stąd pozostałe pola EducationDto są None, nie
    zgadywane."""
    if not education_field_of_study:
        return []

    return [
        {
            "institution": None,
            "degree": None,
            "field_of_study": education_field_of_study,
            "graduation_year": None,
        }
    ]


def build_unified_record(
    heuristic_result: dict[str, Any],
    validator: TechStackValidator,
) -> dict[str, Any]:
    """Składa CVStructuredRecord wyłącznie z wyników heurystyki (bez LLM) -
    patrz heuristic/manager.py za ekstrakcję i heuristic/segmentation.py za
    podział na sekcje, które to umożliwiają."""
    heuristic_phones: list[str] = heuristic_result.get("phones", [])
    heuristic_phone: str | None = heuristic_phones[0] if heuristic_phones else None

    work_experience = [
        _heuristic_candidate_to_work_experience_dto(candidate)
        for candidate in heuristic_result.get("work_experience_candidates", [])
    ]
    total_experience_months: int = heuristic_result.get("total_experience_months", 0)
    heuristic_tech_stack = heuristic_result.get("tech_stack", [])

    return {
        "personal_info": {
            # full_name/location: heurystyka słownikowa nie potrafi
            # wiarygodnie wyciągnąć wolnego tekstu bez NER. linkedin_url
            # natomiast jest regexem po ustandaryzowanym linku (patrz
            # extractors/linkedin.py) - to się da zrobić bez NER.
            "full_name": None,
            "email": heuristic_result.get("email"),
            "phone": heuristic_phone,
            "location": None,
            "linkedin_url": heuristic_result.get("linkedin_url"),
        },
        "summary": None,
        "total_experience_months": total_experience_months,
        "seniority_estimate": estimate_seniority(total_experience_months),
        "work_experience": [
            build_work_experience_entry(entry, validator) for entry in work_experience
        ],
        "skills": {
            "hard": build_hard_skills(work_experience, heuristic_tech_stack, validator),
            # extract_soft_skill_tags zwraca już znormalizowane slugi (np.
            # "ownership", "communication") - ten sam słownik co dla ogłoszeń
            # o pracę, więc po stronie kandydata i oferty porównujemy to samo.
            "soft": heuristic_result.get("soft_skill_tags", []),
            "all_tech_stack_flat": build_flat_tech_stack(
                heuristic_tech_stack, validator
            ),
        },
        "education": _build_education_from_heuristic(
            heuristic_result.get("education_field_of_study")
        ),
        "languages": heuristic_result.get("languages", []),
        "certifications": heuristic_result.get("certifications", []),
        "validation": {
            "warnings": [],
            "field_confidence": {
                "email": "heuristic" if heuristic_result.get("email") else None,
                "phone": "heuristic" if heuristic_phone else None,
            },
        },
    }
