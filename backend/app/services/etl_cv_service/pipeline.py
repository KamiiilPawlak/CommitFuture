from typing import Any

from loguru import logger

from app.schema.cv_llm import CvLlmDto
from app.services.etl_cv_service.cleaning import clean_ocr_text
from app.services.etl_cv_service.heuristic.manager import (
    HeuristicExtractionManager,
)
from app.services.etl_cv_service.llm.client import OllamaLLMClient
from app.services.etl_cv_service.normalization import CVTextNormalizer


class CVPipelineOrchestrator:
    def __init__(
        self,
        normalizer: CVTextNormalizer | None = None,
        heuristic_manager: HeuristicExtractionManager | None = None,
        llm_client: OllamaLLMClient | None = None,
    ) -> None:
        self.normalizer = normalizer or CVTextNormalizer()
        self.heuristic_manager = heuristic_manager or HeuristicExtractionManager()
        self.llm_client = llm_client or OllamaLLMClient()

    async def process_cv(self, raw_text: str) -> dict[str, Any]:
        """Krok 1: Czyszczenie, normalizacja oraz ekstrakcja heurystyczna."""
        if not raw_text or not raw_text.strip():
            logger.warning("[ETL Orchestrator] Otrzymano pusty tekst CV.")
            return self.heuristic_manager.extract_all("")

        logger.info("[ETL Orchestrator] Rozpoczynanie przetwarzania CV...")

        cleaned_text = clean_ocr_text(raw_text)

        normalized_text = self.normalizer.normalize_text(cleaned_text)

        logger.debug("[ETL Orchestrator] Uruchamianie ekstrakcji heurystycznej...")
        heuristic_result = self.heuristic_manager.extract_all(normalized_text)

        llm_result: CvLlmDto | None = None

        try:
            logger.debug("[ETL Orchestrator] Wysyłanie zapytania do Ollama LLM...")
            llm_result = await self.llm_client.parse_cv(normalized_text)
        except Exception as error:
            logger.warning(
                f"[ETL Orchestrator] Błąd połączenia lub przetwarzania LLM: {error}. "
                "Kontynuowanie wyłącznie z danymi z heurystyki."
            )

        return {**heuristic_result, "llm_result": llm_result}
