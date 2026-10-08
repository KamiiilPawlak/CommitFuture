import json

import pytest

from app.services.cv_pipeline.transform.pipeline import CVPipelineOrchestrator

SAMPLE_RAW_CV = """
JAN KOWALSKI
Email: jan.kowalski@example.com | Tel: +48 123-456-789
LinkedIn: linkedin.com/in/jankowalski

DOŚWIADCZENIE:
- Python Developer w Firmie X (styczeń 2022 - obecnie)
  * Pisanie mikroserwisów w FastAPI, PostgreSQL, Docker, Redis.
- Junior Backend Dev w Firmie Y (01.2020 - 12.2021)
  * Praca z Django, Git, Linux, REST API.

UMIEJĘTNOŚCI:
Python, FastAPI, SQLModel, Docker, Git, PostgreSQL, PyTest, English B2
"""


@pytest.mark.asyncio
async def test_cv_pipeline_orchestration() -> None:
    orchestrator = CVPipelineOrchestrator()

    result = await orchestrator.process_cv(SAMPLE_RAW_CV)

    llm_res = result.get("llm_result")

    # Asercje
    assert result["email"] == "jan.kowalski@example.com"
    assert "Python" in result.get("tech_stack", []) or "python" in [
        t.lower() for t in result.get("tech_stack", [])
    ]

    print("\n" + "=" * 20 + " CAŁKOWITY WYNIK ETL " + "=" * 20)  # noqa: T201

    result_to_print = dict(result)
    if llm_res and hasattr(llm_res, "model_dump"):
        result_to_print["llm_result"] = llm_res.model_dump()

    print(json.dumps(result_to_print, indent=2, ensure_ascii=False, default=str))  # noqa: T201
