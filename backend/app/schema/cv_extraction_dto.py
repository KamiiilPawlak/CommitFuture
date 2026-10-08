from pydantic import BaseModel, Field


class WorkExperienceDto(BaseModel):
    company: str | None = Field(default=None, description="Nazwa firmy lub organizacji")
    role: str | None = Field(default=None, description="Stanowisko / Rola zawodowa")
    start_date: str | None = Field(
        default=None, description="Data rozpoczęcia, np. YYYY-MM lub YYYY"
    )
    end_date: str | None = Field(
        default=None, description="Data zakończenia lub 'Present' / 'Obecnie'"
    )
    responsibilities: list[str] = Field(
        default_factory=list, description="Kluczowe obowiązki i osiągnięcia"
    )
    skills_used: list[str] = Field(
        default_factory=list,
        description="Technologie i narzędzia używane konkretnie na tym stanowisku (nie globalnie w całym CV)",
    )


class EducationDto(BaseModel):
    institution: str | None = Field(
        default=None, description="Nazwa uczelni lub szkoły"
    )
    degree: str | None = Field(
        default=None, description="Uzyskany tytuł (Inżynier, Magister, Licencjat)"
    )
    field_of_study: str | None = Field(
        default=None, description="Kierunek lub specjalizacja"
    )
    graduation_year: int | None = Field(
        default=None, description="Rok ukończenia nauki"
    )


class LanguageDto(BaseModel):
    language: str = Field(..., description="Nazwa języka obcego")
    level: str | None = Field(
        default=None,
        description="Poziom znajomości wg CEFR (np. A2, B2, C1) lub opisowy",
    )


