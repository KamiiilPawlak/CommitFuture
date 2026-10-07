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


class PersonalInfoDto(BaseModel):
    full_name: str | None = Field(default=None, description="Imię i nazwisko kandydata")
    email: str | None = Field(default=None, description="Adres e-mail")
    phone: str | None = Field(default=None, description="Numer telefonu")
    location: str | None = Field(default=None, description="Miasto / Kraj zamieszkania")
    linkedin_url: str | None = Field(
        default=None, description="Link do profilu LinkedIn"
    )


class ProjectDto(BaseModel):
    name: str = Field(..., description="Nazwa projektu")
    description: str | None = Field(
        default=None, description="Krótki opis celu projektu"
    )
    technologies: list[str] = Field(
        default_factory=list, description="Technologie użyte w projekcie"
    )


class CvLlmDto(BaseModel):
    """Główny obiekt DTO do odebrania ustrukturyzowanej odpowiedzi z LLM."""

    personal_info: PersonalInfoDto = Field(description="Dane osobowe i kontaktowe")
    summary: str | None = Field(
        default=None, description="Podsumowanie zawodowe lub profil kandydata"
    )
    hard_skills: list[str] = Field(
        default_factory=list,
        description="Wyłącznie technologie, języki programowania, frameworki, bazy danych i narzędzia (np. Python, Docker, SQL, Git)",
    )
    soft_skills: list[str] = Field(
        default_factory=list,
        description="Umiejętności miękkie (np. praca w zespole, komunikatywność)",
    )
    work_experience: list[WorkExperienceDto] = Field(
        default_factory=list, description="Historia zatrudnienia"
    )
    projects: list[ProjectDto] = Field(
        default_factory=list, description="Projekty komercyjne lub własne"
    )
    education: list[EducationDto] = Field(
        default_factory=list, description="Historia wykształcenia"
    )
    languages: list[LanguageDto] = Field(
        default_factory=list, description="Znajomość języków obcych"
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="Wyłącznie oficjalne dyplomy, licencje, zdane egzaminy i ukończone kursy z certyfikatem (np. AWS Certified, CCNA). NIE wpisuj tu zwykłych umiejętności technicznych!",
    )
