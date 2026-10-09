from typing import Any
from uuid import uuid4

import pytest

from app.services.cv_pipeline.processing_service import CVProcessingService
from app.services.cv_pipeline.transform.dictionaries.validator import TechStackValidator


class FakeOrchestrator:
    def __init__(self, process_cv_result: dict[str, Any]) -> None:
        self._result = process_cv_result
        self.tech_stack_validator = TechStackValidator()

    async def process_cv(self, _raw_text: str) -> dict[str, Any]:
        return self._result


class FailingOrchestrator:
    async def process_cv(self, _raw_text: str) -> dict[str, Any]:
        msg = "boom"
        raise RuntimeError(msg)


def _capture_store(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def fake_store(
        cv_document_id: Any, *, structured_data: dict[str, Any], status: str
    ) -> None:
        captured["cv_document_id"] = cv_document_id
        captured["structured_data"] = structured_data
        captured["status"] = status

    monkeypatch.setattr(CVProcessingService, "_store", staticmethod(fake_store))
    return captured


async def test_process_and_store_builds_structured_data_without_duplicating_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cv_document_id = uuid4()
    orchestrator = FakeOrchestrator(
        {
            "email": "jan@test.com",
            "phones": [],
            "dates": [],
            "tech_stack": [],
            "job_titles": [],
            "total_experience_months": 12,
            "total_experience_years": 1.0,
            "work_experience_candidates": [
                {
                    "start_date": None,
                    "end_date": None,
                    "is_current": False,
                    "job_title": "Dev",
                    "skills_used": [],
                }
            ],
        }
    )
    service = CVProcessingService(orchestrator=orchestrator)
    captured = _capture_store(monkeypatch)

    await service.process_and_store(cv_document_id, "raw text")

    assert captured["cv_document_id"] == cv_document_id
    assert captured["status"] == "completed"
    assert "cv_document_id" not in captured["structured_data"]
    assert "status" not in captured["structured_data"]
    assert "personal_info" not in captured["structured_data"]
    assert captured["structured_data"]["work_experience"][0]["role"] == "Dev"


async def test_process_and_store_marks_failed_on_orchestrator_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CVProcessingService(orchestrator=FailingOrchestrator())
    captured = _capture_store(monkeypatch)

    await service.process_and_store(uuid4(), "raw text")

    assert captured["status"] == "failed"
    assert captured["structured_data"] == {}


async def test_process_and_store_completed_status_on_empty_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator = FakeOrchestrator(
        {
            "email": None,
            "phones": [],
            "dates": [],
            "tech_stack": [],
            "job_titles": [],
            "total_experience_months": 0,
            "total_experience_years": 0.0,
        }
    )
    service = CVProcessingService(orchestrator=orchestrator)
    captured = _capture_store(monkeypatch)

    await service.process_and_store(uuid4(), "")

    assert captured["status"] == "completed"
    assert "status" not in captured["structured_data"]
    assert captured["structured_data"]["work_experience"] == []
