from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlmodel import Session

from app.core.config import settings
from app.models.cv_document import CVDocumentLake
from app.repositories.cv_repository import CVRepository
from app.services.cv_pipeline import recovery as recovery_module


def _make_lake_document(repository: CVRepository) -> CVDocumentLake:
    return repository.create_lake_record(
        filename="cv.pdf",
        file_path="storage/cv.pdf",
        file_size=1234,
        mime_type="application/pdf",
    )


def _age_structured_record(
    db_session: Session, cv_document_id: Any, *, minutes_old: int
) -> None:
    repository = CVRepository(db_session)
    record = repository.get_structured_by_lake_id(cv_document_id)
    assert record is not None
    record.processed_at = datetime.now(UTC) - timedelta(minutes=minutes_old)
    db_session.add(record)
    db_session.flush()


async def test_recover_stale_pending_requeues_task_when_raw_text_exists(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = CVRepository(db_session)
    lake_record = _make_lake_document(repository)
    repository.create_raw_text_record(
        lake_id=lake_record.id,
        raw_text="Jan Kowalski, Python developer",
        character_count=30,
        word_count=4,
        page_count=1,
        extraction_tool="pdfplumber",
        metadata_json=None,
    )
    repository.upsert_structured_record(
        cv_document_id=lake_record.id, structured_data=None, status="pending"
    )
    _age_structured_record(
        db_session,
        lake_record.id,
        minutes_old=settings.STALE_PENDING_THRESHOLD_MINUTES + 1,
    )

    delayed_calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "app.services.cv_pipeline.tasks.process_cv_task.delay",
        lambda cv_document_id, raw_text: delayed_calls.append(
            (cv_document_id, raw_text)
        ),
    )

    recovery_module.recover_stale_pending_cv_documents(session=db_session)

    assert delayed_calls == [(str(lake_record.id), "Jan Kowalski, Python developer")]

    record = repository.get_structured_by_lake_id(lake_record.id)
    assert record is not None
    assert record.status == "pending"
    assert record.recovery_attempts == 1


async def test_recover_stale_pending_marks_failed_without_raw_text(
    db_session: Session,
) -> None:
    repository = CVRepository(db_session)
    lake_record = _make_lake_document(repository)
    repository.upsert_structured_record(
        cv_document_id=lake_record.id, structured_data=None, status="pending"
    )
    _age_structured_record(
        db_session,
        lake_record.id,
        minutes_old=settings.STALE_PENDING_THRESHOLD_MINUTES + 1,
    )

    recovery_module.recover_stale_pending_cv_documents(session=db_session)

    record = repository.get_structured_by_lake_id(lake_record.id)
    assert record is not None
    assert record.status == "failed"


async def test_recover_stale_pending_marks_failed_after_max_attempts(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = CVRepository(db_session)
    lake_record = _make_lake_document(repository)
    repository.create_raw_text_record(
        lake_id=lake_record.id,
        raw_text="Jan Kowalski, Python developer",
        character_count=30,
        word_count=4,
        page_count=1,
        extraction_tool="pdfplumber",
        metadata_json=None,
    )
    repository.upsert_structured_record(
        cv_document_id=lake_record.id, structured_data=None, status="pending"
    )
    for _ in range(settings.STALE_PENDING_MAX_ATTEMPTS):
        repository.increment_recovery_attempts(lake_record.id)
    _age_structured_record(
        db_session,
        lake_record.id,
        minutes_old=settings.STALE_PENDING_THRESHOLD_MINUTES + 1,
    )

    delayed_calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "app.services.cv_pipeline.tasks.process_cv_task.delay",
        lambda cv_document_id, raw_text: delayed_calls.append(
            (cv_document_id, raw_text)
        ),
    )

    recovery_module.recover_stale_pending_cv_documents(session=db_session)

    assert delayed_calls == []
    record = repository.get_structured_by_lake_id(lake_record.id)
    assert record is not None
    assert record.status == "failed"


async def test_get_stale_pending_ignores_fresh_and_non_pending_records(
    db_session: Session,
) -> None:
    repository = CVRepository(db_session)

    fresh_pending = _make_lake_document(repository)
    repository.upsert_structured_record(
        cv_document_id=fresh_pending.id, structured_data=None, status="pending"
    )

    stale_completed = _make_lake_document(repository)
    repository.upsert_structured_record(
        cv_document_id=stale_completed.id, structured_data={}, status="completed"
    )

    stale_pending = _make_lake_document(repository)
    repository.upsert_structured_record(
        cv_document_id=stale_pending.id, structured_data=None, status="pending"
    )

    _age_structured_record(db_session, stale_completed.id, minutes_old=60)
    _age_structured_record(db_session, stale_pending.id, minutes_old=60)

    threshold = datetime.now(UTC) - timedelta(minutes=10)
    results = repository.get_stale_pending(older_than=threshold)

    assert [r.cv_document_id for r in results] == [stale_pending.id]
