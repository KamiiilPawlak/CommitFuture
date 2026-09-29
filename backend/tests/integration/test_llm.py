import pytest
from loguru import logger

from app.services.etl_cv_service.llm.client import OllamaLLMClient

SAMPLE_RAW_CV = """
Jan Kowalski
Email: jan.kowalski@example.com | Tel: +48 500 600 700 | Kraków, Polska
LinkedIn: linkedin.com/in/jankowalski

Podsumowanie:
Programista Python z 2-letnim doświadczeniem w tworzeniu aplikacji webowych i mikroserwisów.

Umiejętności techniczne:
Python 3.12, FastAPI, PostgreSQL, React.js, TypeScript, Docker, Git, REST API, Linux, Redis

Doświadczenie zawodowe:
01.2024 - Obecnie
Python Developer | TechCorp Sp. z o.o.
- Tworzenie API w FastAPI oraz SQLModel
- Optymalizacja zapytań SQL i praca z bazami PostgreSQL
- Wdrażanie kontenerów Docker na środowiska stagingowe

06.2023 - 12.2023
Junior Web Developer | SoftApp
- Pisanie komponentów w React, TypeScript i Tailwind CSS
- Integracja z zewnętrznymi API REST

Wykształcenie:
2021 - 2025
Politechnika Krakowska - Informatyka Stosowana, Inżynier

Języki:
- Angielski: B2 (zaawansowany)
- Niemiecki: A1
"""


@pytest.mark.asyncio
async def test_ollama_cv_parsing_integration() -> None:
    logger.info("Inicjalizacja klienta Ollama z qwen2.5:3b...")
    client = OllamaLLMClient(
        base_url="http://localhost:11434",
        model_name="qwen2.5:3b",
        timeout=90.0,
    )

    result = await client.parse_cv(SAMPLE_RAW_CV)

    logger.success("Otrzymano i sparsowano odpowiedź!")
    print(result.model_dump_json(indent=2))  # noqa: T201

    assert result.personal_info.full_name == "Jan Kowalski"
    assert result.personal_info.email == "jan.kowalski@example.com"
    assert len(result.work_experience) == 2
    assert len(result.hard_skills) > 0
