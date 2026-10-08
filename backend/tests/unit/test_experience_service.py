from datetime import date

import pytest

from app.services.cv_pipeline.transform.heuristic.domain.experience_service import (
    ExperienceService,
)
from app.services.cv_pipeline.transform.heuristic.domain.models import (
    DateRange,
    ExperienceMetrics,
)


@pytest.fixture
def service() -> ExperienceService:
    return ExperienceService()


def test_calculate_experience_empty_list(service: ExperienceService) -> None:
    """Test zachowania dla pustej listy wejściowej."""
    result: ExperienceMetrics = service.calculate_experience([])

    assert result.total_days == 0
    assert result.total_months == 0
    assert result.total_years == 0.0
    assert result.min_date is None
    assert result.max_date is None


def test_calculate_experience_single_job(service: ExperienceService) -> None:
    """Test pojedynczego okresu zatrudnienia (np. równy 1 rok)."""
    ranges = [DateRange(start_date=date(2022, 1, 1), end_date=date(2022, 12, 31))]

    result: ExperienceMetrics = service.calculate_experience(ranges)

    assert result.total_days == 365
    assert result.total_months == 12
    assert result.total_years == 1.0
    assert result.min_date == date(2022, 1, 1)
    assert result.max_date == date(2022, 12, 31)


def test_calculate_experience_overlapping_dates(service: ExperienceService) -> None:
    """
    Test nakładających się okresów pracy (dwie prace w tym samym czasie):
    - Praca A: 2020-01-01 do 2021-06-30
    - Praca B: 2021-01-01 do 2021-12-31
    Łącznie powina wyjść ciągła praca od 2020-01-01 do 2021-12-31 (2 lata = 731 dni).
    """
    ranges = [
        DateRange(
            start_date=date(2020, 1, 1), end_date=date(2021, 6, 1)
        ),  # czerwiec rozciągnięty do 2021-06-30
        DateRange(
            start_date=date(2021, 1, 1), end_date=date(2021, 12, 1)
        ),  # grudzień rozciągnięty do 2021-12-31
    ]

    result: ExperienceMetrics = service.calculate_experience(ranges)

    assert result.min_date == date(2020, 1, 1)
    assert result.max_date == date(2021, 12, 31)
    assert result.total_years == 2.0


def test_calculate_experience_is_current(service: ExperienceService) -> None:
    """Test dla pracy trwającej nadal (is_current=True)."""
    ranges = [DateRange(start_date=date.today(), is_current=True)]

    result: ExperienceMetrics = service.calculate_experience(ranges)

    assert result.min_date == date.today()
    assert result.max_date == date.today()
    assert result.total_days == 1


def test_calculate_experience_invalid_dates_filtered_out(
    service: ExperienceService,
) -> None:
    """Test ignorowania wpisów z błędnymi datami (start_date > end_date lub brak start_date)."""
    ranges = [
        DateRange(start_date=None, end_date=date(2022, 1, 1)),
        DateRange(
            start_date=date(2023, 1, 1), end_date=date(2020, 1, 1)
        ),  # Odwrotne daty
    ]

    result: ExperienceMetrics = service.calculate_experience(ranges)

    assert result.total_days == 0
    assert result.min_date is None
