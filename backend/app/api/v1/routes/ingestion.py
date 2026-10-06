from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from loguru import logger
from sqlmodel import Session

from app.db.database import get_session
from app.repositories.cv_repository import CVRepository
from app.schema.ingestion_dto import CVIngestionResponse, CVStructuredDataResponse
from app.services.etl_cv_service.processing_service import (
    CVProcessingService,
    get_cv_processing_service,
)
from app.services.ingestion_service.ingestion_service import (
    IngestionService,
    get_ingestion_service,
)

router = APIRouter(prefix="/cv", tags=["CV Ingestion"])


@router.post(
    "/upload",
    response_model=CVIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Przesłanie pliku CV i uruchomienie OCR",
    description="Zapisuje plik PDF na dysku, rejestruje metadane w Data Lake, wykonuje OCR/ekstrakcję i zapisuje surowy tekst.",
)
async def upload_cv_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
    processing_service: CVProcessingService = Depends(get_cv_processing_service),
) -> CVIngestionResponse:
    logger.info(f"Otrzymano żądanie POST /cv/upload  plik: {file.filename}")

    try:
        lake_record, raw_text_record = await ingestion_service.process_cv_document(file)

        background_tasks.add_task(
            processing_service.process_and_store,
            lake_record.id,
            raw_text_record.raw_text,
        )

        return CVIngestionResponse(
            message="Dokument CV został pomyślnie przetworzony.",
            cv_document_id=lake_record.id,
            mime_type=lake_record.mime_type,
            original_name=lake_record.original_filename,
            character_count=raw_text_record.character_count,
            word_count=raw_text_record.word_count,
            raw_text=raw_text_record.raw_text,
        )

    except ValueError as val_err:
        logger.warning(f"Błąd walidacji podczas wysyłania CV: {val_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as err:
        logger.error(
            f"Nieoczekiwany błąd w procesie ETL dla pliku {file.filename}: {err}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Wystąpił błąd podczas przetwarzania dokumentu CV.",
        ) from err


@router.get(
    "/{cv_document_id}/structured",
    response_model=CVStructuredDataResponse,
    summary="Pobranie ustrukturyzowanych danych CV",
    description="Zwraca zawartość tabeli cv_structured_data dla wskazanego dokumentu.",
)
async def get_cv_structured_data(
    cv_document_id: UUID,
    session: Session = Depends(get_session),
) -> CVStructuredDataResponse:
    repository = CVRepository(session)
    structured_record = repository.get_structured_by_lake_id(cv_document_id)

    if structured_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono ustrukturyzowanych danych dla podanego dokumentu CV.",
        )

    return CVStructuredDataResponse(
        cv_document_id=structured_record.cv_document_id,
        status=structured_record.status,
        structured_data=structured_record.structured_data,
        processed_at=structured_record.processed_at,
    )
