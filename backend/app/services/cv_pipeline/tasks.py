import asyncio
from uuid import UUID

from app.celery_app import celery_app
from app.services.cv_pipeline.processing_service import CVProcessingService


@celery_app.task(name="cv_pipeline.process_cv")
def process_cv_task(cv_document_id: str, raw_text: str) -> None:
    service = CVProcessingService()
    asyncio.run(service.process_and_store(UUID(cv_document_id), raw_text))
