import json
from typing import Any
from uuid import uuid4

import pytest

from app.services.job_pipline.processing_service import JobPostingProcessingService


class FakeParseResult:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def model_dump_json(self) -> str:
        return json.dumps(self._data)


def _capture_store(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def fake_store(
        job_posting_id: Any, *, structured_data: dict[str, Any] | None, status: str
    ) -> None:
        captured["job_posting_id"] = job_posting_id
        captured["structured_data"] = structured_data
        captured["status"] = status

    monkeypatch.setattr(
        JobPostingProcessingService, "_store", staticmethod(fake_store)
    )
    return captured


async def test_process_and_store_marks_completed_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job_posting_id = uuid4()
    captured = _capture_store(monkeypatch)
    monkeypatch.setattr(
        "app.services.job_pipline.processing_service.parse_job_posting",
        lambda _raw_text: FakeParseResult({"min_seniority": "mid"}),
    )

    service = JobPostingProcessingService()
    await service.process_and_store(job_posting_id, "raw job posting text")

    assert captured["job_posting_id"] == job_posting_id
    assert captured["status"] == "completed"
    assert captured["structured_data"] == {"min_seniority": "mid"}


async def test_process_and_store_marks_failed_on_parser_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_store(monkeypatch)

    def _raise(_raw_text: str) -> None:
        msg = "boom"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        "app.services.job_pipline.processing_service.parse_job_posting", _raise
    )

    service = JobPostingProcessingService()
    await service.process_and_store(uuid4(), "raw job posting text")

    assert captured["status"] == "failed"
    assert captured["structured_data"] is None
