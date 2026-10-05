from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.cv_document import CVDocumentLake
from app.models.cv_raw_text import CVRawText
from app.models.cv_structured_data import CVStructuredData


class CVRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_lake_record(
        self,
        filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
    ) -> CVDocumentLake:
        lake_record = CVDocumentLake(
            original_filename=filename,
            storage_path=file_path,
            file_size_bytes=file_size,
            mime_type=mime_type,
        )

        self.session.add(lake_record)
        self.session.flush()
        return lake_record

    def create_raw_text_record(  # noqa: PLR0913
        self,
        *,
        lake_id: UUID,
        raw_text: str,
        character_count: int,
        word_count: int,
        page_count: int,
        extraction_tool: str,
        metadata_json: dict[str, Any] | None,
    ) -> CVRawText:
        raw_cv_record = CVRawText(
            cv_document_id=lake_id,
            raw_text=raw_text,
            character_count=character_count,
            word_count=word_count,
            page_count=page_count,
            extraction_tool=extraction_tool,
            metadata_json=metadata_json,
            extracted_at=datetime.now(UTC),
        )

        self.session.add(raw_cv_record)
        self.session.flush()
        return raw_cv_record

    def get_lake_by_id(self, lake_id: UUID) -> CVDocumentLake | None:
        return self.session.get(CVDocumentLake, lake_id)

    def get_raw_text_by_lake_id(self, lake_id: UUID) -> CVRawText | None:
        statement = select(CVRawText).where(CVRawText.cv_document_id == lake_id)
        return self.session.exec(statement).first()

    def upsert_structured_record(
        self,
        *,
        cv_document_id: UUID,
        structured_data: dict[str, Any],
        status: str,
    ) -> CVStructuredData:
        existing = self.session.get(CVStructuredData, cv_document_id)

        if existing is not None:
            existing.structured_data = structured_data
            existing.status = status
            existing.processed_at = datetime.now(UTC)
            self.session.add(existing)
            self.session.flush()
            return existing

        structured_record = CVStructuredData(
            cv_document_id=cv_document_id,
            structured_data=structured_data,
            status=status,
        )
        self.session.add(structured_record)
        self.session.flush()
        return structured_record

    def get_structured_by_lake_id(self, lake_id: UUID) -> CVStructuredData | None:
        return self.session.get(CVStructuredData, lake_id)

    def get_user_documents(self, user_id: UUID) -> Sequence[CVDocumentLake]:
        statement = select(CVDocumentLake).where(CVDocumentLake.id == user_id)
        return self.session.exec(statement).all()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def refresh(self, instance: object) -> None:
        self.session.refresh(instance)
