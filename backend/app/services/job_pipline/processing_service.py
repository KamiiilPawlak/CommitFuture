from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from loguru import logger
from sqlmodel import Session

from app.db.database import engine
from app.repositories.job_posting_repository import JobPostingRepository
from app.services.job_pipline.transform.parse_job_posting import parse_job_posting


class JobPostingProcessingService:
    async def process_and_store(self, job_posting_id: UUID, raw_text: str) -> None:
        logger.info(f"Start przetwarzania ogłoszenia o pracę {job_posting_id}")

        try:
            result = parse_job_posting(raw_text)
        except Exception as error:
            logger.error(
                f"Nieoczekiwany błąd parsera ogłoszenia {job_posting_id}: {error}"
            )
            self._store(job_posting_id, structured_data=None, status="failed")
            return

        structured_data: dict[str, Any] = json.loads(result.model_dump_json())

        self._store(job_posting_id, structured_data=structured_data, status="completed")

        logger.info(f"Zakończono przetwarzanie ogłoszenia {job_posting_id}")

    @staticmethod
    def _store(
        job_posting_id: UUID, *, structured_data: dict[str, Any] | None, status: str
    ) -> None:
        with Session(engine) as session:
            repository = JobPostingRepository(session)
            repository.update_structured_data(
                job_posting_id=job_posting_id,
                structured_data=structured_data,
                status=status,
            )
            repository.commit()
