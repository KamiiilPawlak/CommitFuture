from typing import Any
from uuid import uuid4

import pytest

from app.schema.cv_llm import CvLlmDto, PersonalInfoDto, WorkExperienceDto
from app.services.etl_cv_service.dictionaries.validator import TechStackValidator
from app.services.etl_cv_service.processing_service import CVProcessingService


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


async def test_process_and_store_injects_cv_document_id_and_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cv_document_id = uuid4()
    llm_result = CvLlmDto(
        personal_info=PersonalInfoDto(email="jan@test.com"),
        work_experience=[
            WorkExperienceDto(
                company="X",
                role="Dev",
                start_date="2020-01",
                end_date=None,
                skills_used=["Python"],
            )
        ],
    )
    orchestrator = FakeOrchestrator(
        {
            "email": "jan@test.com",
            "phones": [],
            "dates": [],
            "tech_stack": [],
            "job_titles": [],
            "total_experience_months": 12,
            "total_experience_years": 1.0,
            "llm_result": llm_result,
            "llm_warnings": [],
            "llm_hard_skills_validated": ["python"],
        }
    )
    service = CVProcessingService(orchestrator=orchestrator)
    captured = _capture_store(monkeypatch)

    await service.process_and_store(cv_document_id, "raw text")

    assert captured["cv_document_id"] == cv_document_id
    assert captured["status"] == "completed"
    assert captured["structured_data"]["cv_document_id"] == str(cv_document_id)
    assert captured["structured_data"]["status"] == "completed"
    assert captured["structured_data"]["personal_info"]["email"] == "jan@test.com"
    assert captured["structured_data"]["work_experience"][0]["company"] == "X"


async def test_process_and_store_marks_failed_on_orchestrator_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CVProcessingService(orchestrator=FailingOrchestrator())
    captured = _capture_store(monkeypatch)

    await service.process_and_store(uuid4(), "raw text")

    assert captured["status"] == "failed"
    assert captured["structured_data"] == {}


async def test_process_and_store_partial_status_without_llm_result(
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
            "llm_result": None,
            "llm_warnings": [],
            "llm_hard_skills_validated": [],
        }
    )
    service = CVProcessingService(orchestrator=orchestrator)
    captured = _capture_store(monkeypatch)

    await service.process_and_store(uuid4(), "")

    assert captured["status"] == "partial"
    assert captured["structured_data"]["status"] == "partial"
    assert captured["structured_data"]["work_experience"] == []
