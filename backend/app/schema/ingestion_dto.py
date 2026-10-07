# app/models/ingestion_dto.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schema.cv_structured_record import CVStructuredRecord


class CVIngestionResponse(BaseModel):
    message: str
    cv_document_id: UUID
    mime_type: str
    original_name: str
    character_count: int
    word_count: int
    raw_text: str = Field(description="Wyekstrahowany tekst po OCR \\ Pdfplumber")


class CVStructuredDataResponse(BaseModel):
    cv_document_id: UUID
    status: str
    structured_data: CVStructuredRecord | None
    processed_at: datetime
