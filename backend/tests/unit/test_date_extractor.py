from datetime import date

from app.services.etl_cv_service.heuristic.extractors.dates import (
    extract_date_ranges,
)


def test_extract_date_ranges_standard_format() -> None:
    text = "Pracowałem w firmie ABC w okresie 01.2020 - 05.2022 na stanowisku Python Developer."

    results = extract_date_ranges(text)

    assert len(results) == 1
    assert results[0]["start_date"] == date(2020, 1, 1)
    assert results[0]["end_date"] == date(2022, 5, 1)
    assert results[0]["is_current"] is False


def test_extract_date_ranges_current_job() -> None:
    text_pl = "Inżynier Oprogramowania, 03.2021 - obecnie"
    text_en = "Software Engineer, 03/2021 to present"

    res_pl = extract_date_ranges(text_pl)
    res_en = extract_date_ranges(text_en)

    assert len(res_pl) == 1
    assert res_pl[0]["start_date"] == date(2021, 3, 1)
    assert res_pl[0]["end_date"] is None
    assert res_pl[0]["is_current"] is True

    assert len(res_en) == 1
    assert res_en[0]["start_date"] == date(2021, 3, 1)
    assert res_en[0]["end_date"] is None
    assert res_en[0]["is_current"] is True


def test_extract_date_ranges_years_only() -> None:
    """Test gdy podane są tylko lata (2018 - 2021)."""
    text = "Edukacja: Politechnika Krakowska (2016 - 2020)"

    results = extract_date_ranges(text)

    assert len(results) == 1
    assert results[0]["start_date"] == date(2016, 1, 1)
    assert results[0]["end_date"] == date(2020, 1, 1)
    assert results[0]["is_current"] is False


def test_extract_date_ranges_multiple_positions() -> None:
    """Test wyciągania wielu zakresów z jednego fragmentu tekstu."""
    text = """
    Doświadczenie:
    - Firma A: 01.2018 - 12.2019
    - Firma B: 01.2020 - obecnie
    """

    results = extract_date_ranges(text)

    assert len(results) == 2
    assert results[0]["start_date"] == date(2018, 1, 1)
    assert results[0]["end_date"] == date(2019, 12, 1)
    assert results[0]["is_current"] is False

    assert results[1]["start_date"] == date(2020, 1, 1)
    assert results[1]["end_date"] is None
    assert results[1]["is_current"] is True


def test_extract_date_ranges_empty_or_invalid() -> None:
    """Test braku dopasowań oraz pustego tekstu."""
    assert extract_date_ranges("") == []
    assert extract_date_ranges("None") == []
    assert extract_date_ranges("Brak jakichkolwiek dat w tym tekście.") == []
