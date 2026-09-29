from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class CVRawText(SQLModel, table=True):
    __tablename__ = "cv_raw_text"

    cv_document_id: UUID = Field(
        foreign_key="cv_document_lake.id",
        primary_key=True,
        description="Identyfikator powiązanego dokumentu w tabeli Data Lake",
    )

    raw_text: str = Field(description="Surowa zawartość tekstowa wyciągnięta z PDF")
    character_count: int = Field(
        description="Łączna liczba znaków w wyciągniętym tekście"
    )
    word_count: int = Field(description="Szacowana liczba słów w tekście")
    page_count: int | None = Field(
        default=None, description="Liczba stron w dokumencie PDF"
    )
    extraction_tool: str = Field(
        default="pdfplumber", description="Nazwa narzędzia/silnika ekstrakcji"
    )
    metadata_json: dict[str, Any] | None = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Metadane strukturalne zwracane przez parser",
    )
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Znacznik czasu wykonania ekstrakcji tekstu",
    )
