from typing import cast

from app.schema.cv_structured_record import CVStructuredRecord
from app.schema.matching_profile import (
    CandidateMatchingProfileDto,
    SeniorityLevel,
    SkillMatchDto,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.education_fields import (
    normalize_field_of_study,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.tech_categories import (
    get_skill_category,
)
from app.services.cv_pipeline.transform.slug import slugify as _slugify

_MONTHS_PER_YEAR = 12

_VALID_SENIORITY_LEVELS: frozenset[str] = frozenset({"junior", "mid", "senior"})
_DEFAULT_SENIORITY_LEVEL: SeniorityLevel = "mid"


def _resolve_seniority(seniority_estimate: str | None) -> SeniorityLevel:
    if seniority_estimate in _VALID_SENIORITY_LEVELS:
        return cast(SeniorityLevel, seniority_estimate)
    return _DEFAULT_SENIORITY_LEVEL


def _months_to_years(months: int | None) -> float | None:
    if not months:
        return None
    return round(months / _MONTHS_PER_YEAR, 1)


def derive_matching_profile(record: CVStructuredRecord) -> CandidateMatchingProfileDto:
    """Przekształca pełny, opisowy CVStructuredRecord (z PII, wolnym tekstem)
    w wąski, znormalizowany profil do porównywania z ogłoszeniem o pracę.
    To czysta transformacja już wyekstrahowanych danych - nie parsuje
    ponownie żadnego tekstu i nie woła żadnego modelu."""
    hard_skills = record.skills.hard if record.skills else []
    soft_skills = record.skills.soft if record.skills else []

    skills = [
        SkillMatchDto(
            name=_slugify(hard_skill.name),
            category=get_skill_category(hard_skill.name),
            years_experience=_months_to_years(hard_skill.months_used),
        )
        for hard_skill in hard_skills
    ]

    education_category = sorted(
        {
            category
            for education in record.education
            if (category := normalize_field_of_study(education.field_of_study))
            is not None
        }
    )

    soft_skill_tags = sorted({_slugify(skill) for skill in soft_skills if skill})

    return CandidateMatchingProfileDto(
        seniority_level=_resolve_seniority(record.seniority_estimate),
        total_experience_years=_months_to_years(record.total_experience_months) or 0.0,
        education_category=education_category,
        skills=skills,
        # Brak jeszcze słownika domen (data_analytics, pharma_gxp...) - patrz
        # feedback z kroku 1. Pole istnieje w schemacie, ale nic go nie
        # wypełnia, dopóki taki słownik nie powstanie.
        domain_tags=[],
        soft_skill_tags=soft_skill_tags,
        certifications=record.certifications,
    )
