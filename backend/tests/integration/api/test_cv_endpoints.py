import io

from fastapi import status
from fastapi.testclient import TestClient

MOCK_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
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
    files = {
        "file": ("jan_kowalski_cv.pdf", io.BytesIO(MOCK_PDF_BYTES), "application/pdf")
    }

    response = client.post("/api/v1/cv/upload", files=files)

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["filename"] == "jan_kowalski_cv.pdf"
