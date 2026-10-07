from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schema.cv_llm import EducationDto, LanguageDto

FieldSource = Literal["heuristic", "llm", "merged"]


class PersonalInfoRecord(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None


class WorkExperienceRecord(BaseModel):
    company: str | None = None
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    responsibilities: list[str] = Field(default_factory=list)
    skills_used: list[str] = Field(default_factory=list)


class HardSkillRecord(BaseModel):
    name: str
    months_used: int | None = None
    last_used: str | None = None
    source: FieldSource


class SkillsRecord(BaseModel):
    hard: list[HardSkillRecord] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)
    all_tech_stack_flat: list[str] = Field(default_factory=list)


class FieldConfidenceRecord(BaseModel):
    email: FieldSource | None = None
    phone: FieldSource | None = None


class ValidationRecord(BaseModel):
    warnings: list[str] = Field(default_factory=list)
    field_confidence: FieldConfidenceRecord = Field(
        default_factory=FieldConfidenceRecord
    )


class CVStructuredRecord(BaseModel):
    """Odzwierciedla dokładnie kształt budowany przez merge.build_unified_record().

    Wszystkie pola opcjonalne z defaultami, bo przy status="failed" (błąd
    pipeline'u w processing_service.py) structured_data w bazie to {} —
    model musi to przyjąć bez walidacyjnego 500.
    """

    cv_document_id: str | None = None
    status: str | None = None
    personal_info: PersonalInfoRecord | None = None
    summary: str | None = None
    total_experience_months: int | None = None
    seniority_estimate: str | None = None
    work_experience: list[WorkExperienceRecord] = Field(default_factory=list)
    skills: SkillsRecord | None = None
    education: list[EducationDto] = Field(default_factory=list)
    languages: list[LanguageDto] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    validation: ValidationRecord | None = None
