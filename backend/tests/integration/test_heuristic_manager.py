from datetime import date
from unittest.mock import MagicMock, patch

from app.services.cv_pipeline.transform.heuristic.manager import (
    HeuristicExtractionManager,
)


@patch("app.services.cv_pipeline.transform.heuristic.domain.experience_calc.date")
def test_heuristic_manager_full_cv_integration(mock_date: MagicMock) -> None:
    mock_date.today.return_value = date(2024, 1, 1)
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

    manager = HeuristicExtractionManager()

    cv_text = """
    Jan Kowalski
    Email: jan.kowalski@example.com | Tel: +48 600 100 200

    Doświadczenie zawodowe:
     Python Developer w Firma ABC (01.2020 - 05.2022)
    - Tworzenie API w FastAPI i Django.
    - Praca z bazami PostgreSQL i Dockerem.

    Senior Python Developer w Firma XYZ (06.2022 - obecnie)
    - Architektura mikroserwisów, React, Kubernetes.
    """

    results = manager.extract_all(cv_text)

    assert results["email"] == "jan.kowalski@example.com"
    assert "+48600100200" in results["phones"]

    assert len(results["dates"]) == 2
    assert results["dates"][0]["start_date"] == date(2020, 1, 1)
    assert results["dates"][0]["end_date"] == date(2022, 5, 1)
    assert results["dates"][0]["is_current"] is False

    assert results["dates"][1]["start_date"] == date(2022, 6, 1)
    assert results["dates"][1]["end_date"] is None
    assert results["dates"][1]["is_current"] is True

    assert results["total_experience_months"] == 48

    tech_stack_lower = [t.lower() for t in results["tech_stack"]]
    assert "fastapi" in tech_stack_lower
    assert "postgresql" in tech_stack_lower
    assert "react" in tech_stack_lower

    job_titles_lower = [j.lower() for j in results["job_titles"]]
    assert "python developer" in job_titles_lower


def test_heuristic_manager_empty_and_invalid_input() -> None:
    manager = HeuristicExtractionManager()

    empty_result = manager.extract_all("")
    assert empty_result["email"] is None
    assert empty_result["phones"] == []
    assert empty_result["dates"] == []
    assert empty_result["tech_stack"] == []
    assert empty_result["job_titles"] == []
    assert empty_result["total_experience_months"] == 0

    none_result = manager.extract_all(None)
    assert none_result["email"] is None
    assert none_result["total_experience_months"] == 0


def test_heuristic_manager_overlapping_dates_calculation() -> None:
    manager = HeuristicExtractionManager()

    text = """
    01.2020 - 12.2020: Python Developer
    06.2020 - 06.2021: Backend Developer
    """

    results = manager.extract_all(text)

    assert results["total_experience_months"] == 18
