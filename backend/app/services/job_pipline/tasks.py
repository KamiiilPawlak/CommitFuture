from uuid import UUID

from app.celery_app import celery_app
from app.core.async_utils import run_coroutine_sync
from app.services.job_pipline.processing_service import JobPostingProcessingService


@celery_app.task(  # type: ignore[untyped-decorator]
    name="job_pipline.process_job_posting",
    acks_late=True,
    soft_time_limit=60,
    time_limit=90,
)
def process_job_posting_task(job_posting_id: str, raw_text: str) -> None:
    service = JobPostingProcessingService()
    run_coroutine_sync(service.process_and_store(UUID(job_posting_id), raw_text))
