import pytest

from app.services.cv_pipeline.transform.heuristic.extractors.dates import (
    DateRange,
    extract_date_ranges,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "Python Developer 2020 - 2023",
            [
                DateRange(
                    start_date="2020-01-01",
                    end_date="2023-01-01",
                    is_current=False,
                )
            ],
        ),
        (
            "Software Engineer 01/2020 - 05/2023",
            [
                DateRange(
                    start_date="2020-01-01",
                    end_date="2023-05-01",
                    is_current=False,
                )
            ],
        ),
        (
            "Backend Developer 2021 – obecnie",  # noqa: RUF001
            [
                DateRange(
                    start_date="2021-01-01",
                    end_date=None,
                    is_current=True,
                )
            ],
        ),
        (
            "Data Scientist 2019 to present",
            [
                DateRange(
                    start_date="2019-01-01",
                    end_date=None,
                    is_current=True,
                )
            ],
        ),
        (
            "Student Informatyki 2022 do nadal",
            [
                DateRange(
                    start_date="2022-01-01",
                    end_date=None,
                    is_current=True,
                )
            ],
        ),
        (
            "Brak informacji o zatrudnieniu",
            [],
        ),
        (
            "",
            [],
        ),
    ],
)
def test_extract_date_ranges(
    text: str,
    expected: list[DateRange],
) -> None:
    assert extract_date_ranges(text) == expected
