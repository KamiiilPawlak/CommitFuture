from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class CVStructuredData(SQLModel, table=True):
    __tablename__ = "cv_structured_data"

    cv_document_id: UUID = Field(
        foreign_key="cv_document_lake.id",
        primary_key=True,
        description="Identyfikator powiązanego dokumentu w tabeli Data Lake",
    )
    structured_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Ustrukturyzowany wynik Etapu B (heurystyki + wynik LLM)",
    )
    status: str = Field(
        default="pending",
        description="Status przetwarzania Etapu B: pending | completed | partial | failed",
    )
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Znacznik czasu zakończenia przetwarzania Etapu B",
    )
