from __future__ import annotations

from typing import Any
from uuid import UUID

from loguru import logger
from sqlmodel import Session

from app.db.database import engine
from app.repositories.cv_repository import CVRepository
from app.services.etl_cv_service.pipeline import CVPipelineOrchestrator


class CVProcessingService:
    def __init__(self, orchestrator: CVPipelineOrchestrator | None = None) -> None:
        self.orchestrator = orchestrator or CVPipelineOrchestrator()

    async def process_and_store(self, cv_document_id: UUID, raw_text: str) -> None:
        logger.info(
            f"[Etap B] Start przetwarzania ETL/NLP dla dokumentu {cv_document_id}"
        )

        try:
            result = await self.orchestrator.process_cv(raw_text)
        except Exception as error:
            logger.error(
                f"[Etap B] Nieoczekiwany błąd pipeline'u dla dokumentu "
                f"{cv_document_id}: {error}"
            )
            self._store(cv_document_id, structured_data={}, status="failed")
            return

        llm_result = result.pop("llm_result", None)
        structured_data: dict[str, Any] = {
            **result,
            "llm_result": llm_result.model_dump() if llm_result else None,
        }
        status = "completed" if llm_result is not None else "partial"

        self._store(cv_document_id, structured_data=structured_data, status=status)

        logger.info(
            f"[Etap B] Zakończono przetwarzanie dokumentu {cv_document_id} "
            f"(status={status})"
        )

    @staticmethod
    def _store(
        cv_document_id: UUID, *, structured_data: dict[str, Any], status: str
    ) -> None:
        with Session(engine) as session:
            repository = CVRepository(session)
            repository.upsert_structured_record(
                cv_document_id=cv_document_id,
                structured_data=structured_data,
                status=status,
            )
            repository.commit()


def get_cv_processing_service() -> CVProcessingService:
    return CVProcessingService()
