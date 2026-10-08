import pytest

from app.services.etl_cv_service.cleaning import clean_ocr_text


@pytest.mark.parametrize(
    "raw_input, expected",
    [
        ("", ""),
        ("   ", ""),
        ("\t\n", ""),
    ],
)
def test_clean_ocr_text_returns_empty_string_for_whitespace_inputs(
    raw_input: str, expected: str
) -> None:
    assert clean_ocr_text(raw_input) == expected


def test_clean_ocr_empty_inputs() -> None:
    # Checks for a completely empty string
    assert clean_ocr_text("") == ""

    # Checks a string consisting of spaces
    assert clean_ocr_text("   ") == ""


def test_clean_ocr_text_replace_hash() -> None:
    assert clean_ocr_text("#eton") == "żeton"
