from collections.abc import Generator
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.database import engine
from app.models.cv_document import CVDocumentLake
from app.models.cv_structured_data import CVStructuredData

JOB_POSTING_TEXT = """
Requirements:
- Python
- FastAPI
"""

COMPLETED_STRUCTURED_DATA: dict[str, Any] = {
    "summary": None,
    "total_experience_months": 36,
    "seniority_estimate": "mid",
    "work_experience": [],
    "skills": {
        "hard": [
            {
                "name": "python",
                "months_used": 36,
                "last_used": "2026",
                "source": "heuristic",
            },
            {
                "name": "fastapi",
                "months_used": 20,
                "last_used": "2026",
                "source": "heuristic",
            },
        ],
        "soft": [],
        "all_tech_stack_flat": ["python", "fastapi"],
    },
    "education": [],
    "languages": [],
    "certifications": [],
    "validation": {"warnings": []},
}


def _seed_cv_document(
    *, status_value: str, structured_data: dict[str, Any] | None
) -> Generator[UUID, None, None]:
    with Session(engine) as session:
        lake = CVDocumentLake(
            original_filename="jan_kowalski_cv.pdf",
            storage_path="storage/test_fixtures/jan_kowalski_cv.pdf",
            file_size_bytes=123,
            mime_type="application/pdf",
        )
        session.add(lake)
        session.flush()

        structured = CVStructuredData(
            cv_document_id=lake.id,
            structured_data=structured_data,
            status=status_value,
        )
        session.add(structured)
        session.commit()
        cv_document_id = lake.id

    yield cv_document_id

    with Session(engine) as session:
        existing_structured = session.get(CVStructuredData, cv_document_id)
        if existing_structured is not None:
            session.delete(existing_structured)
        existing_lake = session.get(CVDocumentLake, cv_document_id)
        if existing_lake is not None:
            session.delete(existing_lake)
        session.commit()


@pytest.fixture
def completed_cv_document_id() -> Generator[UUID, None, None]:
    yield from _seed_cv_document(
        status_value="completed", structured_data=COMPLETED_STRUCTURED_DATA
    )


@pytest.fixture
def pending_cv_document_id() -> Generator[UUID, None, None]:
    yield from _seed_cv_document(status_value="pending", structured_data=None)


def test_match_returns_result_for_completed_cv(
    client: TestClient, completed_cv_document_id: UUID
) -> None:
    response = client.post(
        "/api/v1/match",
        json={
            "cv_document_id": str(completed_cv_document_id),
            "job_posting_raw_text": JOB_POSTING_TEXT,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["skill_coverage"] == 1.0
    assert data["matched_skills"] == ["fastapi", "python"]
    assert data["missing_skills"] == []


def test_match_returns_404_for_unknown_cv_document(client: TestClient) -> None:
    response = client.post(
        "/api/v1/match",
        json={
            "cv_document_id": str(uuid4()),
            "job_posting_raw_text": JOB_POSTING_TEXT,
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_match_returns_409_when_cv_processing_not_complete(
    client: TestClient, pending_cv_document_id: UUID
) -> None:
    response = client.post(
        "/api/v1/match",
        json={
            "cv_document_id": str(pending_cv_document_id),
            "job_posting_raw_text": JOB_POSTING_TEXT,
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT


def test_match_rejects_empty_job_posting_text(
    client: TestClient, completed_cv_document_id: UUID
) -> None:
    response = client.post(
        "/api/v1/match",
        json={
            "cv_document_id": str(completed_cv_document_id),
            "job_posting_raw_text": "",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
