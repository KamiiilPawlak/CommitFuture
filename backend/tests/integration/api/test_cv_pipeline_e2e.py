import io
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db.database import engine
from app.main import app
from app.services.cv_pipeline.extract.ingestion_service import (
    IngestionService,
    get_ingestion_service,
)

RAW_CV_TEXT = """
Jan Kowalski
Python Developer

Doświadczenie zawodowe:
Firma X, Python Developer, 2020-01 - obecnie
Umiejętności: Python, FastAPI, PostgreSQL
"""


def _build_fake_ingestion_service() -> Generator[IngestionService, None, None]:
    file_service = MagicMock()
    file_service.save_pdf_file = AsyncMock(
        return_value=("jan_kowalski_cv.pdf", "fake/path/jan_kowalski_cv.pdf", 1024)
    )
    file_service.read_file = AsyncMock(return_value=b"%PDF-fake-bytes")
    file_service.delete_file = AsyncMock(return_value=None)

    ocr_service = MagicMock()
    ocr_service.process_document = AsyncMock(return_value=(RAW_CV_TEXT, 1))

    with Session(engine) as session:
        yield IngestionService(
            session=session, file_service=file_service, ocr_service=ocr_service
        )


@pytest.fixture
def client_with_fake_ocr() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_ingestion_service] = _build_fake_ingestion_service

    with TestClient(app) as c:
        yield c

    del app.dependency_overrides[get_ingestion_service]


def test_cv_upload_is_processed_end_to_end_and_readable_via_structured_endpoint(
    client_with_fake_ocr: TestClient,
) -> None:
    files = {
        "file": ("jan_kowalski_cv.pdf", io.BytesIO(b"%PDF-fake-bytes"), "application/pdf")
    }

    upload_response = client_with_fake_ocr.post("/api/v1/cv/upload", files=files)
    assert upload_response.status_code == status.HTTP_201_CREATED
    cv_document_id = upload_response.json()["cv_document_id"]

    structured_response = client_with_fake_ocr.get(
        f"/api/v1/cv/{cv_document_id}/structured"
    )

    assert structured_response.status_code == status.HTTP_200_OK
    data = structured_response.json()
    assert data["status"] == "completed"

    structured_data = data["structured_data"]
    assert structured_data is not None
    assert "python" in structured_data["skills"]["all_tech_stack_flat"]
    assert "fastapi" in structured_data["skills"]["all_tech_stack_flat"]


def test_cv_stats_endpoint_counts_completed_document_after_processing(
    client_with_fake_ocr: TestClient,
) -> None:
    files = {
        "file": ("jan_kowalski_cv.pdf", io.BytesIO(b"%PDF-fake-bytes"), "application/pdf")
    }

    client_with_fake_ocr.post("/api/v1/cv/upload", files=files)

    stats_response = client_with_fake_ocr.get("/api/v1/cv/stats")

    assert stats_response.status_code == status.HTTP_200_OK
    assert stats_response.json()["completed"] >= 1
