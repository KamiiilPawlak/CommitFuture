# app/models/ingestion_dto.py
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


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
    structured_data: dict[str, Any] | None
    processed_at: datetime
