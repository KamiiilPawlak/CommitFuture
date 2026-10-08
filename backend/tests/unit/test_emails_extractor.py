from app.services.cv_pipeline.transform.heuristic.extractors.emails import (
    extract_email,
)


def test_extract_email_standard() -> None:
    text = "Kontakt: jan.kowalski@example.com lub telefoniczny."
    assert extract_email(text) == "jan.kowalski@example.com"


def test_extract_email_case_insensitivity_and_stripping() -> None:
    text = "Napisz na JAN.KOWALSKI@DOMAIN.CO.UK w dowolnej chwili."
    assert extract_email(text) == "jan.kowalski@domain.co.uk"


def test_extract_email_with_special_characters() -> None:
    text = "Email: user.name+tag-123@sub.domain-test.io"
    assert extract_email(text) == "user.name+tag-123@sub.domain-test.io"


def test_extract_email_multiple_returns_first() -> None:
    text = "Glowny: first@test.com, zapasowy: second@test.com"
    assert extract_email(text) == "first@test.com"


def test_extract_email_none_or_empty_text() -> None:
    assert extract_email("") is None
    assert extract_email("Brak adresu e-mail w tym tekście 123-456-789.") is None
    assert extract_email("Niepoprawny: user@domain") is None
