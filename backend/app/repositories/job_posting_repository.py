from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlmodel import Session

from app.models.job_posting import JobPosting


class JobPostingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, raw_text: str) -> JobPosting:
        job_posting = JobPosting(raw_text=raw_text)
        self.session.add(job_posting)
        self.session.flush()
        return job_posting

    def get_by_id(self, job_posting_id: UUID) -> JobPosting | None:
        return self.session.get(JobPosting, job_posting_id)

    def update_structured_data(
        self,
        *,
        job_posting_id: UUID,
        structured_data: dict[str, Any] | None,
        status: str,
    ) -> JobPosting | None:
        job_posting = self.session.get(JobPosting, job_posting_id)
        if job_posting is None:
            return None

        job_posting.structured_data = structured_data
        job_posting.status = status
        job_posting.processed_at = datetime.now(UTC)
        self.session.add(job_posting)
        self.session.flush()
        return job_posting

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def refresh(self, instance: object) -> None:
        self.session.refresh(instance)
