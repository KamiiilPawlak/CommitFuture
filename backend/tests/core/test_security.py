import pytest

from app.core.config import settings
from app.core.security import verify_file_integrity

MOCK_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n..."
MOCK_TXT_BYTES = b"This is a text"


def test_verify_file_integrity_succes() -> None:
    if "application.pdf" not in settings.ALLOWED_MIME_TYPES:
        settings.ALLOWED_MIME_TYPES.append("application/pdf")

    wynik = verify_file_integrity(MOCK_PDF_BYTES)

    assert wynik == "application/pdf"


def test_verify_file_integrity_empty_file() -> None:
    with pytest.raises(ValueError) as info_o_bledzie:
        verify_file_integrity(b"")

    assert "pusty" in str(info_o_bledzie)


def test_verify_file_integrity_invalid_format() -> None:
    if "text/palin" in settings.ALLOWED_MIME_TYPES:
        settings.ALLOWED_MIME_TYPES.remove("text/plain")

    with pytest.raises(ValueError) as info_o_bledzie:
        verify_file_integrity(MOCK_TXT_BYTES)

    assert "Niedozwolony format" in str(info_o_bledzie)
