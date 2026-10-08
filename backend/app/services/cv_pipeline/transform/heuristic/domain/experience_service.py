from datetime import date

from app.services.etl_cv_service.heuristic.domain.experience_calc import (
    convert_extracted_range_to_dates,
    merge_overlapping_ranges,
)
from app.services.etl_cv_service.heuristic.domain.models import (
    DateRange,
    ExperienceMetrics,
)


class ExperienceService:
    def calculate_experience(self, raw_ranges: list[DateRange]) -> ExperienceMetrics:
        valid_ranges: list[tuple[date, date]] = []
        for range_item in raw_ranges:
            converted = convert_extracted_range_to_dates(range_item)
            if converted:
                valid_ranges.append(converted)

        if not valid_ranges:
            return ExperienceMetrics(
                total_days=0,
                total_months=0,
                total_years=0.0,
                min_date=None,
                max_date=None,
            )

        merged = merge_overlapping_ranges(valid_ranges)

        total_days = sum((end - start).days + 1 for start, end in merged)
        total_months = round(total_days / 30.4375)
        total_years = round(total_days / 365.25, 1)

        min_date = min(start for start, _ in merged)
        max_date = max(end for _, end in merged)

        return ExperienceMetrics(
            total_days=total_days,
            total_months=total_months,
            total_years=total_years,
            min_date=min_date,
            max_date=max_date,
        )
