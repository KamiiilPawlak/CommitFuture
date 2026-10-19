import io
from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient

REAL_CV_PDF_PATH = (
    Path(__file__).resolve().parents[4] / "test_file" / "Curriculum Vitae - Jan Kowalski.pdf"
)
MOCK_TXT_BYTES = "Oto zwykły plik tekstowy, który nie jest akceptowany.".encode()


def test_upload_cv_invalid_file_format_returns_400(client: TestClient) -> None:
    files = {"file": ("test_cv.txt", io.BytesIO(MOCK_TXT_BYTES), "text/plain")}

    response = client.post("/api/v1/cv/upload", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert "detail" in data
    assert "Niedozwolony format" in data["detail"]


def test_upload_cv_empty_file_returns_400(client: TestClient) -> None:
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}

    response = client.post("/api/v1/cv/upload", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "pusty" in response.json()["detail"].lower()


def test_upload_cv_success(client: TestClient) -> None:
    pdf_bytes = REAL_CV_PDF_PATH.read_bytes()
    files = {"file": ("jan_kowalski_cv.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = client.post("/api/v1/cv/upload", files=files)

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["original_name"] == "jan_kowalski_cv.pdf"
