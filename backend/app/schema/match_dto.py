from uuid import UUID

from pydantic import BaseModel, Field


class MatchRequestDto(BaseModel):
    cv_document_id: UUID
    job_posting_raw_text: str = Field(min_length=1)


class MatchResultDto(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    seniority_match: bool
    skill_coverage: float = Field(ge=0.0, le=1.0)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    domain_overlap: list[str] = Field(default_factory=list)
    soft_skill_overlap: list[str] = Field(default_factory=list)
    education_match: bool
