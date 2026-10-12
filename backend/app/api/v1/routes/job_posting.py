from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from loguru import logger
from sqlmodel import Session

from app.db.database import get_session
from app.repositories.job_posting_repository import JobPostingRepository
from app.schema.job_posting_dto import (
    JobPostingStructuredResponse,
    JobPostingSubmitRequest,
    JobPostingSubmitResponse,
)
from app.services.job_pipline.processing_service import (
    JobPostingProcessingService,
    get_job_posting_processing_service,
)

router = APIRouter(prefix="/job-postings", tags=["Job Posting Ingestion"])


@router.post(
    "",
    response_model=JobPostingSubmitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_job_posting(
    payload: JobPostingSubmitRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    processing_service: JobPostingProcessingService = Depends(
        get_job_posting_processing_service
    ),
) -> JobPostingSubmitResponse:
    logger.info("Otrzymano żądanie POST /job-postings")

    repository = JobPostingRepository(session)
    job_posting = repository.create(payload.raw_text)
    repository.commit()

    background_tasks.add_task(
        processing_service.process_and_store,
        job_posting.id,
        job_posting.raw_text,
    )

    return JobPostingSubmitResponse(
        message="Ogłoszenie o pracę zostało przyjęte do przetworzenia.",
        job_posting_id=job_posting.id,
        status=job_posting.status,
    )


@router.get(
    "/{job_posting_id}",
    response_model=JobPostingStructuredResponse,
)
async def get_job_posting(
    job_posting_id: UUID,
    session: Session = Depends(get_session),
) -> JobPostingStructuredResponse:
    repository = JobPostingRepository(session)
    job_posting = repository.get_by_id(job_posting_id)

    if job_posting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono ogłoszenia o pracę o podanym identyfikatorze.",
        )

    return JobPostingStructuredResponse(
        job_posting_id=job_posting.id,
        status=job_posting.status,
        structured_data=job_posting.structured_data,
        processed_at=job_posting.processed_at,
    )
