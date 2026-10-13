import asyncio
from uuid import UUID

from app.celery_app import celery_app
from app.services.cv_pipeline.processing_service import CVProcessingService


@celery_app.task(
    name="cv_pipeline.process_cv",
    acks_late=True,
    soft_time_limit=60,
    time_limit=90,
)
def process_cv_task(cv_document_id: str, raw_text: str) -> None:
    service = CVProcessingService()
    asyncio.run(service.process_and_store(UUID(cv_document_id), raw_text))


@celery_app.task(name="_resilience_probe", acks_late=True)
def _resilience_probe(seconds: int) -> str:
    import time

    time.sleep(seconds)
    return "done"
