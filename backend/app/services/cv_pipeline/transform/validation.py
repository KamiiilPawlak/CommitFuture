import re
from typing import Any

from app.schema.cv_llm import CvLlmDto


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value)


def detect_llm_hallucinations(
    llm_result: CvLlmDto | None,
    heuristic_result: dict[str, Any],
    raw_text: str,
) -> list[str]:

    if llm_result is None:
        return []

    warnings: list[str] = []
    normalized_text = raw_text.lower()

    llm_email = llm_result.personal_info.email
    if llm_email and llm_email.lower() not in normalized_text:
        warnings.append(
            f"LLM zwrócił email '{llm_email}', którego nie znaleziono w tekście CV."
        )

    llm_phone = llm_result.personal_info.phone
    if llm_phone:
        llm_phone_digits = _digits_only(llm_phone)
        text_digits = _digits_only(raw_text)
        if llm_phone_digits and llm_phone_digits not in text_digits:
            warnings.append(
                f"LLM zwrócił telefon '{llm_phone}', którego nie znaleziono w tekście CV."
            )

    heuristic_email = heuristic_result.get("email")
    if heuristic_email and llm_email and heuristic_email.lower() != llm_email.lower():
        warnings.append(
            f"Rozbieżność email: heurystyka='{heuristic_email}' vs LLM='{llm_email}'."
        )

    return warnings
