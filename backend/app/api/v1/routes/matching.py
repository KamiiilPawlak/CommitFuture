from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import ValidationError
from sqlmodel import Session

from app.db.database import get_session
from app.schema.match_dto import MatchRequestDto
from app.schema.matching_profile import MatchResultDto
from app.services.matching_engine.service import (
    CVNotFoundError,
    CVProcessingNotCompleteError,
    match_candidate_to_job_posting,
)

router = APIRouter(prefix="/match", tags=["Matching"])


@router.post(
    "",
    response_model=MatchResultDto,
    summary="Policzenie dopasowania CV do ogłoszenia o pracę",
    description=(
        "Liczy wynik dopasowania on-demand, bez zapisu do bazy - bierze gotowy "
        "profil kandydata z już przetworzonego CV oraz surowy tekst ogłoszenia "
        "podany w żądaniu."
    ),
)
async def match_cv_to_job_posting(
    payload: MatchRequestDto,
    session: Session = Depends(get_session),
) -> MatchResultDto:
    logger.info(f"Otrzymano żądanie POST /match dla CV {payload.cv_document_id}")

    try:
        return match_candidate_to_job_posting(
            session,
            cv_document_id=payload.cv_document_id,
            job_posting_raw_text=payload.job_posting_raw_text,
        )
    except CVNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except CVProcessingNotCompleteError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except ValidationError as val_err:
        logger.error(
            f"[match] Zapisane structured_data dla CV {payload.cv_document_id} "
            f"nie pasuje do aktualnego schematu: {val_err}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Ustrukturyzowane dane tego CV są w nieobsługiwanym formacie "
                "i wymagają ponownego przetworzenia."
            ),
        ) from val_err
