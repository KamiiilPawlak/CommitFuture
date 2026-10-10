import regex as re

from app.schema.matching_profile import (
    JobPostingMatchingDto,
    RequiredSkillDto,
    SeniorityLevel,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.domains import (
    extract_domain_tags,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.education_fields import (
    extract_field_of_study_categories,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.soft_skills import (
    extract_soft_skill_tags,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.tech_categories import (
    get_skill_category,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.tech_stack import (
    extract_tech_stack_with_offsets,
)
from app.services.cv_pipeline.transform.heuristic.segmentation import (
    JOB_POSTING_SECTION_HEADER_PATTERNS,
    find_sections,
    offset_in_spans,
    spans_for_type,
)
from app.services.cv_pipeline.transform.slug import slugify

_REQUIREMENTS_WEIGHT = 1.0
_RESPONSIBILITIES_ONLY_WEIGHT = 0.6

_SENIORITY_KEYWORD_PATTERNS: list[tuple[re.Pattern[str], SeniorityLevel]] = [
    (
        re.compile(r"(?i)\b(senior|lead|principal|staff|starszy|główny[ay]?)\b"),
        "senior",
    ),
    (
        re.compile(r"(?i)\b(mid[\s-]?level|regular|średni[oa]?zaawansowan[ya])\b"),
        "mid",
    ),
    (
        re.compile(
            r"(?i)\b(junior|entry[\s-]?level|młodsz[ya]|stażyst[a-z]*|intern)\b"
        ),
        "junior",
    ),
]
_DEFAULT_MIN_SENIORITY: SeniorityLevel = "mid"


def _detect_min_seniority(text: str) -> SeniorityLevel:
    """Szuka słów-kluczy poziomu seniority w całym ogłoszeniu. Kolejność ma
    znaczenie: ogłoszenie, które wspomina 'Senior-level' gdziekolwiek, ma
    pierwszeństwo przed np. przypadkowym 'mid' w innym kontekście."""
    for pattern, level in _SENIORITY_KEYWORD_PATTERNS:
        if pattern.search(text):
            return level
    return _DEFAULT_MIN_SENIORITY


def _extract_required_skills(
    text: str,
    requirements_spans: list[tuple[int, int]],
    responsibilities_spans: list[tuple[int, int]],
    nice_to_have_spans: list[tuple[int, int]],
) -> list[RequiredSkillDto]:
    """Technologia wymieniona w sekcji Requirements dostaje wagę 1.0, w
    Responsibilities (ale nie w Requirements) 0.6 - w prawdziwych
    ogłoszeniach stos technologiczny często pada w opisie obowiązków, nie w
    samej liście wymagań. Technologia wyłącznie w Nice to have NIE trafia
    tutaj (to opcjonalne, nie wymagane). Brak wykrytych nagłówków sekcji =
    całe ogłoszenie liczy się jako wymagania (fallback jak w segmentacji CV).
    """
    has_sections = bool(
        requirements_spans or responsibilities_spans or nice_to_have_spans
    )

    weight_per_skill: dict[str, float] = {}
    for name, offset in extract_tech_stack_with_offsets(text):
        if not has_sections:
            weight = _REQUIREMENTS_WEIGHT
        else:
            in_requirements = offset_in_spans(offset, requirements_spans)
            in_responsibilities = offset_in_spans(offset, responsibilities_spans)
            in_nice_to_have = offset_in_spans(offset, nice_to_have_spans)

            if in_nice_to_have and not in_requirements and not in_responsibilities:
                continue
            if not in_requirements and not in_responsibilities:
                # Dopasowanie poza rozpoznaną sekcją (np. we wstępie
                # ogłoszenia) - zbyt niejednoznaczne, żeby uznać za wymóg.
                continue

            weight = (
                _REQUIREMENTS_WEIGHT
                if in_requirements
                else _RESPONSIBILITIES_ONLY_WEIGHT
            )

        weight_per_skill[name] = max(weight_per_skill.get(name, 0.0), weight)

    return [
        RequiredSkillDto(
            name=slugify(name), category=get_skill_category(name), weight=weight
        )
        for name, weight in sorted(weight_per_skill.items())
    ]


def parse_job_posting(text: str) -> JobPostingMatchingDto:
    """Parsuje treść ogłoszenia o pracę do JobPostingMatchingDto - bez LLM,
    tymi samymi słownikami/mechanizmem segmentacji co dla CV, więc technologie
    i kategorie po obu stronach (kandydat/ogłoszenie) są porównywalne 1:1."""
    if not text or not text.strip():
        return JobPostingMatchingDto(min_seniority=_DEFAULT_MIN_SENIORITY)

    sections = find_sections(text, header_patterns=JOB_POSTING_SECTION_HEADER_PATTERNS)
    requirements_spans = spans_for_type(sections, "requirements")
    responsibilities_spans = spans_for_type(sections, "responsibilities")
    nice_to_have_spans = spans_for_type(sections, "nice_to_have")

    return JobPostingMatchingDto(
        min_seniority=_detect_min_seniority(text),
        required_skills=_extract_required_skills(
            text, requirements_spans, responsibilities_spans, nice_to_have_spans
        ),
        nice_to_have_domain_tags=extract_domain_tags(text),
        education_requirement=extract_field_of_study_categories(text),
        soft_skill_tags=extract_soft_skill_tags(text),
    )
