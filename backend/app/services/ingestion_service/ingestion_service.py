from __future__ import annotations

from typing import Any, cast

from fastapi import Depends, UploadFile
from loguru import logger
from sqlmodel import Session

from app.db.database import get_session
from app.models.cv_document import CVDocumentLake
from app.models.cv_raw_text import CVRawText
from app.repositories.cv_repository import CVRepository

from .file_service import StorageService
from .ocr_service import OCRService


class IngestionService:
    def __init__(
        self,
        session: Session,
        file_service: StorageService | None = None,
        ocr_service: OCRService | None = None,
    ) -> None:
        self.repository = CVRepository(session)
        self.file_service = file_service or StorageService()
        self.ocr_service = ocr_service or OCRService()

    async def process_cv_document(
        self, file: UploadFile
    ) -> tuple[CVDocumentLake, CVRawText]:
        logger.info(f"Start ETL pipeline dla pliku: {file.filename}")

        (
            original_filename,
            destination_path,
            file_size,
        ) = await self.file_service.save_pdf_file(file)

        try:
            lake_record = self.repository.create_lake_record(
                filename=original_filename,
                file_path=destination_path,
                file_size=file_size,
                mime_type=cast(Any, file.content_type or "application/pdf"),
            )

            file_bytes = await self.file_service.read_file(destination_path)
            raw_text, page_count = await self.ocr_service.process_document(
                content=file_bytes,
                mime_type=lake_record.mime_type,
            )

            char_count, word_count, metadata = self._build_text_metrics(raw_text)

            raw_text_record = self.repository.create_raw_text_record(
                lake_id=lake_record.id,
                raw_text=raw_text,
                character_count=char_count,
                word_count=word_count,
                page_count=page_count,
                extraction_tool="pdfplumber/pytesseract",
                metadata_json=metadata,
            )

            self.repository.commit()
            self.repository.refresh(raw_text_record)

            logger.info(f"ETL zakończony sukcesem dla pliku: {original_filename}")

            return lake_record, raw_text_record  # noqa: TRY300

        except Exception as error:
            logger.error(f"Błąd ETL dla ścieżki {destination_path}. Rollback: {error}")
            self.repository.rollback()
            await self.file_service.delete_file(destination_path)
            raise

    @staticmethod
    def _build_text_metrics(raw_text: str) -> tuple[int, int, dict[str, Any]]:
        if not raw_text:
            return 0, 0, {"status": "empty", "char_count": 0, "word_count": 0}

        char_count = len(raw_text)
        word_count = len(raw_text.split())
        metadata = {
            "status": "success",
            "char_count": char_count,
            "word_count": word_count,
        }
        return char_count, word_count, metadata


def get_ingestion_service(
    session: Session = Depends(get_session),
) -> IngestionService:
    return IngestionService(session=session)
