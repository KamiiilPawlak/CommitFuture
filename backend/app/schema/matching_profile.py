from typing import Literal

from pydantic import BaseModel, Field

SkillCategory = Literal[
    "frontend", "backend", "database", "cloud", "devops", "testing", "other"
]

SeniorityLevel = Literal["junior", "mid", "senior"]


class SkillMatchDto(BaseModel):
    name: str = Field(description="Znormalizowany slug technologii, np. 'fastapi'")
    category: SkillCategory = Field(
        default="other", description="Kategoria technologii do grupowania w matchingu"
    )
    years_experience: float | None = Field(
        default=None, description="Lata doświadczenia z tą technologią"
    )


class CandidateMatchingProfileDto(BaseModel):
    seniority_level: SeniorityLevel = Field(
        description="Znormalizowany poziom doświadczenia kandydata"
    )
    total_experience_years: float = Field(
        description="Łączne doświadczenie zawodowe w latach"
    )
    education_category: list[str] = Field(
        default_factory=list,
        description="Znormalizowane kategorie kierunków wykształcenia",
    )
    skills: list[SkillMatchDto] = Field(default_factory=list)
    domain_tags: list[str] = Field(
        default_factory=list,
        description="Tagi branżowe/domenowe wywnioskowane z CV (np. 'data_analytics')",
    )
    soft_skill_tags: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class RequiredSkillDto(BaseModel):
    name: str = Field(description="Znormalizowany slug technologii")
    category: SkillCategory = Field(default="other")
    weight: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Waga wymagania w ogłoszeniu"
    )


class JobPostingMatchingDto(BaseModel):
    min_seniority: SeniorityLevel = Field(
        description="Minimalny wymagany poziom doświadczenia"
    )
    required_skills: list[RequiredSkillDto] = Field(default_factory=list)
    nice_to_have_domain_tags: list[str] = Field(default_factory=list)
    education_requirement: list[str] = Field(
        default_factory=list,
        description="Akceptowane znormalizowane kategorie kierunków wykształcenia",
    )
    soft_skill_tags: list[str] = Field(default_factory=list)
