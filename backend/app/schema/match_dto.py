from uuid import UUID

from pydantic import BaseModel, Field


class MatchRequestDto(BaseModel):
    cv_document_id: UUID
    job_posting_raw_text: str = Field(min_length=1)
