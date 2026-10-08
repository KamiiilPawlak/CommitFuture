from typing import Any

from app.services.cv_pipeline.transform.heuristic.allocation import (
    allocate_matches_to_nearest_preceding_anchor,
    pick_nearest_label_per_anchor,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.certifications import (
    extract_certifications,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.education_fields import (
    extract_field_of_study,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.job_titles import (
    JOB_TITLES_DICTIONARY,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.languages import (
    extract_languages,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.lookup_engine import (
    FlashLookupEngine,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.soft_skills import (
    extract_soft_skill_tags,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.tech_categories import (
    get_skill_category,
)
from app.services.cv_pipeline.transform.heuristic.dictionary.tech_stack import (
    TECH_STACK_DICTIONARY,
)
from app.services.cv_pipeline.transform.heuristic.domain.experience_service import (
    ExperienceService,
)
from app.services.cv_pipeline.transform.heuristic.domain.models import DateRange
from app.services.cv_pipeline.transform.heuristic.extractors import (
    extract_date_ranges,
    extract_email,
    extract_phones,
)
from app.services.cv_pipeline.transform.heuristic.extractors.dates import (
    extract_date_ranges_with_offsets,
)
from app.services.cv_pipeline.transform.heuristic.segmentation import (
    find_sections,
    offset_in_spans,
    spans_for_type,
)


class HeuristicExtractionManager:
    def __init__(self) -> None:
        combined_keywords: dict[str, list[str]] = {
            **TECH_STACK_DICTIONARY,
            **JOB_TITLES_DICTIONARY,
        }
        self.lookup_engine = FlashLookupEngine(keywords_map=combined_keywords)
        self.experience_service = ExperienceService()

        self._tech_keys = set(TECH_STACK_DICTIONARY.keys())
        self._job_keys = set(JOB_TITLES_DICTIONARY.keys())

    def extract_all(self, raw_text: str | None) -> dict[str, Any]:
        if not raw_text or not raw_text.strip():
            return {
                "email": None,
                "phones": [],
                "dates": [],
                "tech_stack": [],
                "job_titles": [],
                "total_experience_months": 0,
                "total_experience_years": 0.0,
                "certifications": [],
                "languages": [],
                "education_field_of_study": None,
                "work_experience_candidates": [],
                "soft_skill_tags": [],
            }

        email = extract_email(raw_text)
        phones = extract_phones(raw_text)
        date_ranges = extract_date_ranges(raw_text)

        matches = self.lookup_engine.extract_matches(raw_text)

        tech_stack = [m for m in matches if m in self._tech_keys]
        job_titles = [m for m in matches if m in self._job_keys]

        sections = find_sections(raw_text)
        experience_spans = spans_for_type(sections, "experience")
        if not experience_spans:
            # Brak wykrytych nagłówków sekcji (np. CV bez jawnej struktury) -
            # zachowujemy dotychczasowe zachowanie i traktujemy cały tekst
            # jako jedną sekcję doświadczenia, żeby nie regresować CV bez
            # nagłówków.
            experience_spans = [(0, len(raw_text))]

        date_ranges_with_offsets = extract_date_ranges_with_offsets(raw_text)
        experience_date_ranges = [
            (date_ranges[index], offsets["offset"])
            for index, offsets in enumerate(date_ranges_with_offsets)
            if offset_in_spans(offsets["offset"], experience_spans)
        ]

        # UWAGA: staż liczony WYŁĄCZNIE z zakresów dat leżących w sekcji
        # Doświadczenie - zakres dat z Edukacji (np. lata studiów) nie może
        # wliczać się w total_experience_months/years, inaczej zawyża to
        # seniority_estimate i total_experience_years na wejściu do matchingu.
        experience_date_range_objs = [
            DateRange(
                start_date=date_range.get("start_date"),
                end_date=date_range.get("end_date"),
                is_current=bool(date_range.get("is_current", False)),
            )
            for date_range, _offset in experience_date_ranges
        ]
        experience = self.experience_service.calculate_experience(
            experience_date_range_objs
        )

        return {
            "email": email,
            "phones": phones,
            "dates": date_ranges,
            "tech_stack": tech_stack,
            "job_titles": job_titles,
            "total_experience_months": experience.total_months,
            "total_experience_years": experience.total_years,
            "certifications": extract_certifications(raw_text),
            "languages": extract_languages(raw_text),
            "education_field_of_study": extract_field_of_study(raw_text),
            "work_experience_candidates": self._build_work_experience_candidates(
                raw_text, experience_spans, experience_date_ranges
            ),
            "soft_skill_tags": extract_soft_skill_tags(raw_text),
        }

    def _build_work_experience_candidates(
        self,
        raw_text: str,
        experience_spans: list[tuple[int, int]],
        experience_date_ranges: list[tuple[dict[str, Any], int]],
    ) -> list[dict[str, Any]]:
        """Bez pomocy LLM odtwarza przypisanie 'ten tytuł stanowiska i te
        technologie należą do tego okresu zatrudnienia' - wyłącznie na
        podstawie pozycji dopasowań w tekście (offsetów), ograniczonej do
        sekcji 'Doświadczenie'. Bez tego ograniczenia zakresy dat z Edukacji
        oraz technologie/tytuły wspomniane w Certyfikatach czy Językach
        "przeciekały" do najbliższego stanowiska pracy (np. "AWS Certified
        Solutions Architect" w sekcji Certyfikaty dawało fałszywe "AWS" jako
        skill i "Solutions Architect" jako tytuł stanowiska).
        """
        if not experience_date_ranges:
            return []

        anchor_offsets = [offset for _dr, offset in experience_date_ranges]

        matches_with_offsets = self.lookup_engine.extract_matches_with_offsets(
            raw_text
        )
        matches_in_experience = [
            (name, offset)
            for name, offset in matches_with_offsets
            if offset_in_spans(offset, experience_spans)
        ]
        tech_with_offsets = [
            (name, offset)
            for name, offset in matches_in_experience
            if name in self._tech_keys
        ]
        job_titles_with_offsets = [
            (name, offset)
            for name, offset in matches_in_experience
            if name in self._job_keys
        ]

        skills_per_anchor = allocate_matches_to_nearest_preceding_anchor(
            tech_with_offsets, anchor_offsets
        )
        job_title_per_anchor = pick_nearest_label_per_anchor(
            job_titles_with_offsets, anchor_offsets
        )

        return [
            {
                "start_date": date_range.get("start_date"),
                "end_date": date_range.get("end_date"),
                "is_current": date_range.get("is_current", False),
                "job_title": job_title_per_anchor.get(index),
                "skills_used": [
                    {"name": skill, "category": get_skill_category(skill)}
                    for skill in skills_per_anchor.get(index, [])
                ],
            }
            for index, (date_range, _offset) in enumerate(experience_date_ranges)
        ]
