import asyncio
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import UUID

from app.celery_app import celery_app
from app.services.cv_pipeline.processing_service import CVProcessingService
from app.services.cv_pipeline.recovery import recover_stale_pending_cv_documents


def _run_coroutine_sync(coroutine: Coroutine[Any, Any, None]) -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coroutine)
        return

    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(asyncio.run, coroutine).result()


@celery_app.task(
    name="cv_pipeline.process_cv",
    acks_late=True,
    soft_time_limit=60,
    time_limit=90,
)
def process_cv_task(cv_document_id: str, raw_text: str) -> None:
    service = CVProcessingService()
    _run_coroutine_sync(service.process_and_store(UUID(cv_document_id), raw_text))


@celery_app.task(name="cv_pipeline.recover_stale_pending")
def recover_stale_pending_task() -> None:
    recover_stale_pending_cv_documents()
