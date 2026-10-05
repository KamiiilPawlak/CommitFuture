import asyncio
from typing import Any

import httpx
from loguru import logger

from app.core.config import settings
from app.schema.cv_llm import CvLlmDto
from app.services.etl_cv_service.llm.prompts import (
    SYSTEM_PROMPT,
    build_cv_extraction_prompt,
)


class OllamaLLMClient:
    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        model_name: str = settings.OLLAMA_MODEL_NAME,
        timeout: float = settings.OLLAMA_TIMEOUT,
        max_retries: int = settings.OLLAMA_MAX_RETRIES,
        retry_backoff_seconds: float = settings.OLLAMA_RETRY_BACKOFF_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds

    async def parse_cv(self, raw_text: str) -> CvLlmDto:
        endpoint = f"{self.base_url}/api/chat"
        prompt = build_cv_extraction_prompt(raw_text)

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "format": CvLlmDto.model_json_schema(),
            "stream": False,
            "options": {
                "temperature": 0.0,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            last_http_error: httpx.HTTPError | None = None

            for attempt in range(1, self.max_retries + 1):
                logger.info(
                    f"Wysyłanie zapytania do Ollama ({self.model_name}), "
                    f"próba {attempt}/{self.max_retries}..."
                )
                try:
                    response = await client.post(endpoint, json=payload)
                    response.raise_for_status()

                    response_data = response.json()
                    content = response_data.get("message", {}).get("content", "{}")

                    logger.success("Pomyślnie odebrano odpowiedź z Ollama")
                    return CvLlmDto.model_validate_json(content)

                except httpx.HTTPError as err:
                    last_http_error = err
                    logger.warning(
                        f"Błąd komunikacji z Ollama API (próba {attempt}/"
                        f"{self.max_retries}): {err}"
                    )
                    if attempt < self.max_retries:
                        backoff = self.retry_backoff_seconds * (2 ** (attempt - 1))
                        await asyncio.sleep(backoff)
                except Exception as err:
                    logger.error(
                        f"Błąd walidacji schematu Pydantic z odpowiedzi LLM: {err}"
                    )
                    msg_0 = f"Failed to parse LLM response to CvLlmDto: {err}"
                    raise ValueError(msg_0) from err

            logger.error(
                f"Błąd komunikacji z Ollama API po {self.max_retries} próbach: "
                f"{last_http_error}"
            )
            msg = f"Ollama integration error after {self.max_retries} attempts: {last_http_error}"
            raise RuntimeError(msg) from last_http_error
