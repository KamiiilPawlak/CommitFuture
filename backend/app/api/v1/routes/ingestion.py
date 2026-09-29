from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from loguru import logger

from app.schema.ingestion_dto import CVIngestionResponse
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
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> CVIngestionResponse:
    logger.info(f"Otrzymano żądanie POST /cv/upload  plik: {file.filename}")

    try:
        lake_record, raw_text_record = await ingestion_service.process_cv_document(file)

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
