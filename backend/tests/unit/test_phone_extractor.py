from app.services.cv_pipeline.transform.heuristic.extractors.phone import (
    extract_phones,
)


def test_extract_phones_standard_polish_formats() -> None:
    text = "Kontakt: +48 600 100 200, tel: 600-100-300 oraz (22) 123 45 67."
    results = extract_phones(text)

    assert len(results) == 3
    assert "+48600100200" in results
    assert "+48600100300" in results
    assert "+48221234567" in results


def test_extract_phones_deduplication() -> None:
    text = "Tel: 600100200 / +48 600 100 200 / 600-100-200"
    results = extract_phones(text)

    assert results == ["+48600100200"]


def test_extract_phones_custom_default_region() -> None:
    text = "UK Contact: 020 7946 0958"
    results = extract_phones(text, default_region="GB")

    assert results == ["+442079460958"]


def test_extract_phones_ignores_invalid_numbers() -> None:
    text = "Kod pocztowy 12-345, NIP 1234567890, krótki ciąg 12345"
    assert extract_phones(text) == []


def test_extract_phones_empty_or_none_input() -> None:
    assert extract_phones("") == []
    assert extract_phones("   ") == []
    assert extract_phones(None) == []
