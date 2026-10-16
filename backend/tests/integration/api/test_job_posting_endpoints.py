from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

JOB_POSTING_TEXT = """
Senior Python Developer

Requirements:
- Python and FastAPI
- PostgreSQL
"""


def test_submit_job_posting_returns_201_with_pending_or_completed_status(
    client: TestClient,
) -> None:
    response = client.post("/api/v1/job-postings", json={"raw_text": JOB_POSTING_TEXT})

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "job_posting_id" in data
    assert data["status"] in {"pending", "completed"}


def test_submit_job_posting_rejects_empty_raw_text(client: TestClient) -> None:
    response = client.post("/api/v1/job-postings", json={"raw_text": ""})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_job_posting_returns_structured_data_after_processing(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/v1/job-postings", json={"raw_text": JOB_POSTING_TEXT}
    )
    job_posting_id = create_response.json()["job_posting_id"]

    response = client.get(f"/api/v1/job-postings/{job_posting_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "completed"
    assert data["structured_data"]["min_seniority"] == "senior"
    skill_names = {
        skill["name"] for skill in data["structured_data"]["required_skills"]
    }
    assert {"python", "fastapi", "postgresql"} <= skill_names


def test_get_job_posting_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get(f"/api/v1/job-postings/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
