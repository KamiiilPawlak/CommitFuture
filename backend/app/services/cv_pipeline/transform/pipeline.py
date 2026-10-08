from typing import Any

from loguru import logger

from app.services.cv_pipeline.transform.cleaning import clean_ocr_text
from app.services.cv_pipeline.transform.dictionaries.validator import TechStackValidator
from app.services.cv_pipeline.transform.heuristic.manager import (
    HeuristicExtractionManager,
)
from app.services.cv_pipeline.transform.normalization import CVTextNormalizer


class CVPipelineOrchestrator:
    def __init__(
        self,
        normalizer: CVTextNormalizer | None = None,
        heuristic_manager: HeuristicExtractionManager | None = None,
        tech_stack_validator: TechStackValidator | None = None,
    ) -> None:
        self.normalizer = normalizer or CVTextNormalizer()
        self.heuristic_manager = heuristic_manager or HeuristicExtractionManager()
        self.tech_stack_validator = tech_stack_validator or TechStackValidator()

    async def process_cv(self, raw_text: str) -> dict[str, Any]:
        """Czyszczenie, normalizacja oraz ekstrakcja heurystyczna - bez LLM."""
        if not raw_text or not raw_text.strip():
            logger.warning("[ETL Orchestrator] Otrzymano pusty tekst CV.")
            return self.heuristic_manager.extract_all("")

        logger.info("[ETL Orchestrator] Rozpoczynanie przetwarzania CV...")

        cleaned_text = clean_ocr_text(raw_text)
        normalized_text = self.normalizer.normalize_text(cleaned_text)

        logger.debug("[ETL Orchestrator] Uruchamianie ekstrakcji heurystycznej...")
        return self.heuristic_manager.extract_all(normalized_text)
