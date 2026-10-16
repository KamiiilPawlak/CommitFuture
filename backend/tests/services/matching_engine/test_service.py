from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.repositories.cv_repository import CVRepository
from app.services.matching_engine.service import (
    CVNotFoundError,
    CVProcessingNotCompleteError,
    match_candidate_to_job_posting,
)

JOB_POSTING_TEXT = """
Requirements:
- Python
- FastAPI
"""

COMPLETED_STRUCTURED_DATA = {
    "summary": None,
    "total_experience_months": 36,
    "seniority_estimate": "mid",
    "work_experience": [],
    "skills": {
        "hard": [
            {"name": "python", "months_used": 36, "last_used": "2026", "source": "heuristic"},
            {"name": "fastapi", "months_used": 20, "last_used": "2026", "source": "heuristic"},
        ],
        "soft": [],
        "all_tech_stack_flat": ["python", "fastapi"],
    },
    "education": [],
    "languages": [],
    "certifications": [],
    "validation": {"warnings": []},
}


def _mock_structured(monkeypatch: pytest.MonkeyPatch, structured: object | None) -> None:
    monkeypatch.setattr(
        CVRepository, "get_structured_by_lake_id", lambda _self, _id: structured
    )


def test_match_candidate_to_job_posting_returns_result_for_completed_cv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    structured = SimpleNamespace(
        status="completed", structured_data=COMPLETED_STRUCTURED_DATA
    )
    _mock_structured(monkeypatch, structured)

    result = match_candidate_to_job_posting(
        session=object(),
        cv_document_id=uuid4(),
        job_posting_raw_text=JOB_POSTING_TEXT,
    )

    assert result.skill_coverage == 1.0
    assert result.matched_skills == ["fastapi", "python"]


def test_match_candidate_to_job_posting_raises_when_cv_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_structured(monkeypatch, None)

    with pytest.raises(CVNotFoundError):
        match_candidate_to_job_posting(
            session=object(),
            cv_document_id=uuid4(),
            job_posting_raw_text=JOB_POSTING_TEXT,
        )


@pytest.mark.parametrize("status_value", ["pending", "failed"])
def test_match_candidate_to_job_posting_raises_when_cv_not_completed(
    monkeypatch: pytest.MonkeyPatch, status_value: str
) -> None:
    structured = SimpleNamespace(status=status_value, structured_data=None)
    _mock_structured(monkeypatch, structured)

    with pytest.raises(CVProcessingNotCompleteError):
        match_candidate_to_job_posting(
            session=object(),
            cv_document_id=uuid4(),
            job_posting_raw_text=JOB_POSTING_TEXT,
        )
