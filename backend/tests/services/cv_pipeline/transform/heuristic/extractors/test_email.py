import pytest

from app.services.etl_cv_service.heuristic.extractors.emails import extract_email


@pytest.mark.parametrize(
    "text, expected_email",
    [
        (
            "Email: jan@example.com",
            "jan@example.com",
        ),
        (
            "Kontakt: Jan.Kowalski@Example.COM",
            "jan.kowalski@example.com",
        ),
        (
            "Możesz napisać na test.user+cv@gmail.com",
            "test.user+cv@gmail.com",
        ),
        (
            "Jan Kowalski Python Developer Email: jan@example.com Phone: +48 123 456 789",
            "jan@example.com",
        ),
        (
            "Brak adresu email tutaj",
            None,
        ),
        (
            "",
            None,
        ),
    ],
)
def test_extract_email(text: str, expected_email: str | None) -> None:
    assert extract_email(text) == expected_email
