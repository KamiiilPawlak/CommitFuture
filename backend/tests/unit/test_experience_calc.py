from datetime import date

from app.services.cv_pipeline.transform.heuristic.domain.experience_calc import (
    convert_extracted_range_to_dates,
    merge_overlapping_ranges,
)
from app.services.cv_pipeline.transform.heuristic.domain.models import DateRange


def test_convert_range_valid_dates() -> None:
    """Test prawidłowej konwersji ze stałymi datami (koniec miesiąca rozciągnięty)."""
    item = DateRange(start_date=date(2021, 5, 10), end_date=date(2022, 2, 1))

    result = convert_extracted_range_to_dates(item)

    assert result == (date(2021, 5, 10), date(2022, 2, 28))


def test_convert_range_leap_year() -> None:
    item = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 2, 10))

    result = convert_extracted_range_to_dates(item)

    assert result == (date(2024, 1, 1), date(2024, 2, 29))


def test_convert_range_is_current() -> None:
    item = DateRange(start_date=date(2023, 1, 1), is_current=True)

    result = convert_extracted_range_to_dates(item)

    assert result == (date(2023, 1, 1), date.today())


def test_convert_range_missing_start_date() -> None:
    item = DateRange(start_date=None, end_date=date(2022, 5, 1))

    assert convert_extracted_range_to_dates(item) is None


def test_convert_range_start_after_end() -> None:
    item = DateRange(start_date=date(2023, 1, 1), end_date=date(2020, 1, 1))

    assert convert_extracted_range_to_dates(item) is None


# ============================================================================
# Testy dla: merge_overlapping_ranges
# ============================================================================


def test_merge_ranges_empty_list() -> None:
    assert merge_overlapping_ranges([]) == []


def test_merge_ranges_no_overlap() -> None:
    ranges = [
        (date(2018, 1, 1), date(2019, 12, 31)),
        (date(2021, 1, 1), date(2022, 12, 31)),
    ]

    merged = merge_overlapping_ranges(ranges)

    assert len(merged) == 2
    assert merged == ranges


def test_merge_ranges_partial_overlap() -> None:
    ranges = [
        (date(2020, 1, 1), date(2021, 6, 30)),
        (date(2021, 1, 1), date(2022, 5, 31)),
    ]

    merged = merge_overlapping_ranges(ranges)

    assert len(merged) == 1
    assert merged == [(date(2020, 1, 1), date(2022, 5, 31))]


def test_merge_ranges_completely_enclosed() -> None:
    ranges = [
        (date(2020, 1, 1), date(2023, 12, 31)),
        (date(2021, 3, 1), date(2021, 9, 30)),
    ]

    merged = merge_overlapping_ranges(ranges)

    assert len(merged) == 1
    assert merged == [(date(2020, 1, 1), date(2023, 12, 31))]


def test_merge_ranges_unsorted_input() -> None:
    ranges = [
        (date(2022, 1, 1), date(2023, 1, 1)),
        (date(2019, 1, 1), date(2020, 6, 1)),
        (date(2020, 1, 1), date(2021, 1, 1)),
    ]

    merged = merge_overlapping_ranges(ranges)

    assert len(merged) == 2
    assert merged == [
        (date(2019, 1, 1), date(2021, 1, 1)),
        (date(2022, 1, 1), date(2023, 1, 1)),
    ]
