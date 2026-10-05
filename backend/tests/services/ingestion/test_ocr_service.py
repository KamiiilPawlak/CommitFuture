from unittest.mock import MagicMock

import pytest

from app.services.ingestion_service.ocr_service import OCRService


@pytest.fixture
def ocr_service() -> OCRService:
    return OCRService()


@pytest.mark.asyncio
async def test_process_document_digital_pdf_success(
    ocr_service: OCRService, mocker: MagicMock
) -> None:
    fake_content = b"fake_pdf_bytes"
    fake_mime = "application/pdf"
    expected_text = "To jest w pelni cyfrowy tekst wyciagniety z PDF przez pdfplumber i ma ponad sto znakow, zeby warunek dlugosci zostal spelniony bez problemu!"

    mock_page = MagicMock()
    mock_page.extract_text.return_value = expected_text

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    mock_open = mocker.patch(
        "app.services.ingestion_service.ocr_service.pdfplumber.open"
    )
    mock_open.return_value.__enter__.return_value = mock_pdf

    mock_tesseract = mocker.patch(
        "app.services.ingestion_service.ocr_service.pytesseract.image_to_string"
    )

    result, page_count = await ocr_service.process_document(fake_content, fake_mime)

    assert result == expected_text
    assert page_count == 1

    mock_open.assert_called_once()

    mock_tesseract.assert_not_called()


@pytest.mark.asyncio
async def test_process_document_image_ocr_success(
    ocr_service: OCRService, mocker: MagicMock
) -> None:
    fake_content = b"fake_image_bytes"
    fake_mime = "image/png"
    expected_ocr_text = "Tekst odczytany przez sztucznego Tesseracta z obrazka PNG"

    mock_tesseract = mocker.patch(
        "app.services.ingestion_service.ocr_service.pytesseract.image_to_string"
    )
    mock_tesseract.return_value = expected_ocr_text

    mock_image_instance = MagicMock()
    mock_open_image = mocker.patch(
        "app.services.ingestion_service.ocr_service.Image.open"
    )
    mock_open_image.return_value = mock_image_instance

    mock_image_instance.convert.return_value = mock_image_instance
    mock_image_instance.filter.return_value = mock_image_instance

    mocker.patch(
        "app.services.ingestion_service.ocr_service.ImageOps.autocontrast",
        return_value=mock_image_instance,
    )

    result, page_count = await ocr_service.process_document(fake_content, fake_mime)

    assert result == expected_ocr_text
    assert page_count == 1

    mock_open_image.assert_called_once()

    mock_tesseract.assert_called_once_with(mock_image_instance, lang="pol+eng")
