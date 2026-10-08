from datetime import date

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class ExperienceMetrics(BaseModel):
    total_days: int = Field(
        ..., description="Całkowita liczba dni stażu bez nakładających się okresów"
    )
    total_months: int = Field(..., description="Liczba miesięcy stażu ")
    total_years: float = Field(
        ..., description="Liczba lat stażu zaokrąglona do 1 miejsca po przecinku"
    )
    min_date: date | None = Field(None, description="Data rozpoczęcia pierwszej pracy")
    max_date: date | None = Field(None, description="Data zakończenia ostatniej pracy")
