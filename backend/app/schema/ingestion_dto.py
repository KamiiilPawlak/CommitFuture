# app/models/ingestion_dto.py
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


class ExtractedMetadata(BaseModel):
    email: str | None = Field(None, description="Wyciągnięty adres email kandydata")
    phone: str | None = Field(None, description="Wyciągnięty numer telefonu kandydata")


class ProcessedCVTO(BaseModel):
    metadata: ExtractedMetadata
    setions: dict[str, str] = Field(
        default_factory=dict, description="Pocięte sekcje CV"
    )
    full_processed_text: str = Field(..., description="Pełny tekst po normalizacji")
