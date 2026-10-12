from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class JobPosting(SQLModel, table=True):
    __tablename__ = "job_posting"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    raw_text: str
    structured_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSONB),
    )
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = Field(default=None)
