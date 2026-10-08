from calendar import monthrange
from datetime import date

from app.services.etl_cv_service.heuristic.domain.models import DateRange


def convert_extracted_range_to_dates(extracted: DateRange) -> tuple[date, date] | None:
    if not extracted.start_date:
        return None

    start_dt: date = extracted.start_date

    if extracted.is_current or not extracted.end_date:
        end_dt: date = date.today()
    else:
        temp_end: date = extracted.end_date
        last_day: int = monthrange(temp_end.year, temp_end.month)[1]
        end_dt = date(temp_end.year, temp_end.month, last_day)

    if start_dt > end_dt:
        return None

    return (start_dt, end_dt)


def merge_overlapping_ranges(
    ranges: list[tuple[date, date]],
) -> list[tuple[date, date]]:
    if not ranges:
        return []

    sorted_ranges = sorted(ranges, key=lambda r: r[0])
    merged = [sorted_ranges[0]]

    for current_start, current_end in sorted_ranges[1:]:
        prev_start, prev_end = merged[-1]

        if current_start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, current_end))
        else:
            merged.append((current_start, current_end))

    return merged
