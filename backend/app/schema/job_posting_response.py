from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schema.matching_profile import JobPostingMatchingDto


class JobPostingSubmitRequest(BaseModel):
    raw_text: str = Field(min_length=1)


class JobPostingSubmitResponse(BaseModel):
    message: str
    job_posting_id: UUID
    status: str


class JobPostingStructuredResponse(BaseModel):
    job_posting_id: UUID
    status: str
    structured_data: JobPostingMatchingDto | None
    processed_at: datetime | None
