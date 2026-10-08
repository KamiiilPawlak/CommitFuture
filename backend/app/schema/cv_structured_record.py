from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schema.cv_extraction_dto import EducationDto, LanguageDto

FieldSource = Literal["heuristic", "llm", "merged"]

_KNOWN_RECORD_KEYS = {
    "cv_document_id",
    "status",
    "personal_info",
    "summary",
    "total_experience_months",
    "seniority_estimate",
    "work_experience",
    "skills",
    "education",
    "languages",
    "certifications",
    "validation",
}


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

    @model_validator(mode="before")
    @classmethod
    def _reject_unrecognized_shape(cls, data: Any) -> Any:
        if not isinstance(data, dict) or not data:
            return data

        if _KNOWN_RECORD_KEYS.isdisjoint(data.keys()):
            msg = (
                "structured_data nie zawiera żadnego rozpoznawalnego pola "
                "aktualnego schematu (personal_info/work_experience/skills/...). "
                "Wygląda na dane w starym formacie sprzed refaktoru merge.py."
            )
            raise ValueError(msg)

        return data
