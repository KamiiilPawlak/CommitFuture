import io
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.models.cv_document import CVDocumentLake
from app.models.cv_raw_text import CVRawText
from app.services.ingestion_service import IngestionService


@pytest.mark.asyncio
async def test_process_cv_document_success() -> None:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        fake_storage_path = temp_file.name

    mock_session = MagicMock()
    mock_storage_service = MagicMock()
    mock_ocr_service = MagicMock()

    mock_storage_service.save_pdf_file = AsyncMock(
        return_value=("test_cv.pdf", fake_storage_path, 1024)
    )
    mock_storage_service.read_file = AsyncMock(return_value=b"%PDF-fake-bytes")

    mock_ocr_service.process_document = AsyncMock(return_value="Sample CV Text")

    fake_lake_record = CVDocumentLake(
        original_filename="test_cv.pdf",
        storage_path=fake_storage_path,
        file_size_bytes=1024,
        mime_type="application/pdf",
    )
    fake_raw_text_record = MagicMock(spec=CVRawText)

    with patch("app.services.ingestion_service.CVRepository") as mock_repo_class:
        mock_repo = mock_repo_class.return_value
        mock_repo.create_lake_record.return_value = fake_lake_record
        mock_repo.create_raw_text_record.return_value = fake_raw_text_record

        service = IngestionService(
            session=mock_session,
            file_service=mock_storage_service,
            ocr_service=mock_ocr_service,
        )

        fake_file = UploadFile(
            filename="test_cv.pdf",
            file=io.BytesIO(b"%PDF-fake-bytes"),
            headers=Headers({"content-type": "application/pdf"}),
        )

        lake_res, raw_res = await service.process_cv_document(file=fake_file)

        mock_storage_service.save_pdf_file.assert_awaited_once_with(fake_file)
        mock_repo.create_lake_record.assert_called_once_with(
            filename="test_cv.pdf",
            file_path=fake_storage_path,
            file_size=1024,
            mime_type="application/pdf",
        )
        mock_repo.commit.assert_called_once()
        mock_repo.refresh.assert_called_once_with(fake_raw_text_record)

        assert lake_res == fake_lake_record
        assert raw_res == fake_raw_text_record
