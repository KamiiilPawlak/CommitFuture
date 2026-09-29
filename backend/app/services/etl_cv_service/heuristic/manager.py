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
from app.services.etl_cv_service.heuristic.domain.experience_calc import (
    convert_extracted_range_to_dates,
    merge_overlapping_ranges,
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

        self._tech_keys = set(TECH_STACK_DICTIONARY.keys())
        self._job_keys = set(JOB_TITLES_DICTIONARY.keys())

    def _calculate_total_experience_months(
        self, raw_dates: list[dict[str, Any]]
    ) -> int:
        valid_date_tuples = []

        for date_dict in raw_dates:
            date_range_obj = DateRange(
                start_date=date_dict.get("start_date"),
                end_date=date_dict.get("end_date"),
                is_current=bool(date_dict.get("is_current", False)),
            )

            converted_tuple = convert_extracted_range_to_dates(date_range_obj)
            if converted_tuple:
                valid_date_tuples.append(converted_tuple)

        merged_ranges = merge_overlapping_ranges(valid_date_tuples)

        total_days = sum((end - start).days + 1 for start, end in merged_ranges)
        return round(total_days / 30.4375)

    def extract_all(self, raw_text: str | None) -> dict[str, Any]:
        if not raw_text or not raw_text.strip():
            return {
                "email": None,
                "phones": [],
                "dates": [],
                "tech_stack": [],
                "job_titles": [],
                "total_experience_months": 0,
            }

        email = extract_email(raw_text)
        phones = extract_phones(raw_text)
        date_ranges = extract_date_ranges(raw_text)

        matches = self.lookup_engine.extract_matches(raw_text)

        tech_stack = [m for m in matches if m in self._tech_keys]
        job_titles = [m for m in matches if m in self._job_keys]

        total_experience_months = self._calculate_total_experience_months(date_ranges)

        return {
            "email": email,
            "phones": phones,
            "dates": date_ranges,
            "tech_stack": tech_stack,
            "job_titles": job_titles,
            "total_experience_months": total_experience_months,
        }
