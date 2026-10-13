from uuid import UUID

from sqlmodel import Session

from app.repositories.cv_repository import CVRepository
from app.schema.cv_structured_record import CVStructuredRecord
from app.schema.matching_profile import MatchResultDto
from app.services.cv_pipeline.transform.derive_matching_profile import (
    derive_matching_profile,
)
from app.services.job_pipline.transform.parse_job_posting import parse_job_posting
from app.services.matching_engine.engine import calculate_match


class CVNotFoundError(Exception):
    """Brak ustrukturyzowanych danych dla podanego cv_document_id."""


class CVProcessingNotCompleteError(Exception):
    """Etap B (ekstrakcja heurystyczna) dla CV jeszcze się nie zakończył."""


def match_candidate_to_job_posting(
    session: Session, *, cv_document_id: UUID, job_posting_raw_text: str
) -> MatchResultDto:
    """Liczy dopasowanie on-demand, bez zapisu wyniku do bazy - patrz decyzja
    w docs/architecture/matching-engine-roadmap.md (Faza 3): matching jest
    deterministyczny i tani (bez LLM), więc liczenie na żądanie jest
    praktycznie bezpłatne i zawsze aktualne względem najnowszego CV."""
    repository = CVRepository(session)
    structured = repository.get_structured_by_lake_id(cv_document_id)

    if structured is None:
        msg = "Nie znaleziono ustrukturyzowanych danych dla podanego dokumentu CV."
        raise CVNotFoundError(msg)

    if structured.status != "completed":
        msg = (
            "Przetwarzanie CV (Etap B) nie jest jeszcze zakończone "
            f"(status: {structured.status})."
        )
        raise CVProcessingNotCompleteError(msg)

    record = CVStructuredRecord(**(structured.structured_data or {}))
    candidate_profile = derive_matching_profile(record)
    job_posting_profile = parse_job_posting(job_posting_raw_text)

    return calculate_match(candidate_profile, job_posting_profile)
