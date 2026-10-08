from typing import Any

from app.services.etl_cv_service.heuristic.dictionary.job_titles import (
    JOB_TITLES_DICTIONARY,
)
from app.services.etl_cv_service.heuristic.dictionary.lookup_engine import (
    FlashLookupEngine,
)
from app.services.etl_cv_service.heuristic.dictionary.tech_stack import (
    TECH_STACK_DICTIONARY,
)
from app.services.etl_cv_service.heuristic.domain.experience_service import (
    ExperienceService,
)
from app.services.etl_cv_service.heuristic.domain.models import DateRange
from app.services.etl_cv_service.heuristic.extractors import (
    extract_date_ranges,
    extract_email,
    extract_phones,
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
            }

        email = extract_email(raw_text)
        phones = extract_phones(raw_text)
        date_ranges = extract_date_ranges(raw_text)

        matches = self.lookup_engine.extract_matches(raw_text)

        tech_stack = [m for m in matches if m in self._tech_keys]
        job_titles = [m for m in matches if m in self._job_keys]

        date_range_objs = [
            DateRange(
                start_date=date_dict.get("start_date"),
                end_date=date_dict.get("end_date"),
                is_current=bool(date_dict.get("is_current", False)),
            )
            for date_dict in date_ranges
        ]
        experience = self.experience_service.calculate_experience(date_range_objs)

        return {
            "email": email,
            "phones": phones,
            "dates": date_ranges,
            "tech_stack": tech_stack,
            "job_titles": job_titles,
            "total_experience_months": experience.total_months,
            "total_experience_years": experience.total_years,
        }
