from __future__ import annotations

from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlmodel import Session

from app.core.config import settings
from app.db.database import engine
from app.models.cv_structured_data import CVStructuredData
from app.repositories.cv_repository import CVRepository


def recover_stale_pending_cv_documents(session: Session | None = None) -> None:
    threshold = datetime.now(UTC) - timedelta(
        minutes=settings.STALE_PENDING_THRESHOLD_MINUTES
    )

    if session is not None:
        _recover_stale_pending(session, threshold)
        return

    with Session(engine) as owned_session:
        _recover_stale_pending(owned_session, threshold)


def _recover_stale_pending(session: Session, threshold: datetime) -> None:
    repository = CVRepository(session)
    stale_records = repository.get_stale_pending(older_than=threshold)

    for record in stale_records:
        _recover_one(repository, record)

    repository.commit()


def _recover_one(repository: CVRepository, record: CVStructuredData) -> None:
    from app.services.cv_pipeline.tasks import process_cv_task  # noqa: PLC0415

    cv_document_id = record.cv_document_id

    if record.recovery_attempts >= settings.STALE_PENDING_MAX_ATTEMPTS:
        logger.error(
            f"[Recovery] Dokument {cv_document_id} przekroczył limit "
            f"{settings.STALE_PENDING_MAX_ATTEMPTS} prób odzyskania z 'pending' "
            "— oznaczam jako failed."
        )
        repository.upsert_structured_record(
            cv_document_id=cv_document_id, structured_data={}, status="failed"
        )
        return

    raw_text_record = repository.get_raw_text_by_lake_id(cv_document_id)
    if raw_text_record is None:
        logger.error(
            f"[Recovery] Brak cv_raw_text dla zawieszonego dokumentu "
            f"{cv_document_id} — nie da się ponowić przetwarzania, oznaczam jako failed."
        )
        repository.upsert_structured_record(
            cv_document_id=cv_document_id, structured_data={}, status="failed"
        )
        return

    repository.increment_recovery_attempts(cv_document_id)
    logger.warning(
        f"[Recovery] Dokument {cv_document_id} zawisł w statusie 'pending' "
        f"dłużej niż {settings.STALE_PENDING_THRESHOLD_MINUTES} min — ponawiam "
        f"przetwarzanie (próba {record.recovery_attempts + 1}/"
        f"{settings.STALE_PENDING_MAX_ATTEMPTS})."
    )
    process_cv_task.delay(str(cv_document_id), raw_text_record.raw_text)
