from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from loguru import logger
from sqlmodel import Session

from app.db.database import engine
from app.repositories.cv_repository import CVRepository
from app.services.cv_pipeline.transform.merge import build_unified_record
from app.services.cv_pipeline.transform.pipeline import CVPipelineOrchestrator


class CVProcessingService:
    def __init__(self, orchestrator: CVPipelineOrchestrator | None = None) -> None:
        self.orchestrator: CVPipelineOrchestrator = (
            orchestrator or CVPipelineOrchestrator()
        )

    async def process_and_store(self, cv_document_id: UUID, raw_text: str) -> None:
        logger.info(
            f"[Etap B] Start przetwarzania ETL/NLP dla dokumentu {cv_document_id}"
        )

        try:
            result: dict[str, Any] = await self.orchestrator.process_cv(raw_text)
        except Exception as error:
            logger.error(
                f"[Etap B] Nieoczekiwany błąd pipeline'u dla dokumentu "
                f"{cv_document_id}: {error}"
            )
            self._store(cv_document_id, structured_data={}, status="failed")
            return

        unified_record: dict[str, Any] = build_unified_record(
            heuristic_result=result,
            validator=self.orchestrator.tech_stack_validator,
        )

        status: str = "completed"

        raw_structured_data: dict[str, Any] = {
            "cv_document_id": str(cv_document_id),
            "status": status,
            **unified_record,
        }

        structured_data: dict[str, Any] = json.loads(
            json.dumps(raw_structured_data, default=str)
        )

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
            repository: CVRepository = CVRepository(session)
            repository.upsert_structured_record(
                cv_document_id=cv_document_id,
                structured_data=structured_data,
                status=status,
            )
            repository.commit()


def get_cv_processing_service() -> CVProcessingService:
    return CVProcessingService()
