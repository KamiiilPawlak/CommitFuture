import pytest

from app.services.etl_cv_service.heuristic.extractors.phone import extract_phones


@pytest.mark.parametrize(
    "input_text,expected_phone",
    [
        ("123456789", ["+48123456789"]),
        ("My number is 123 456 789.", ["+48123456789"]),
        ("+48 123456789", ["+48123456789"]),
        ("123-456-789", ["+48123456789"]),
        ("Contact +48 123456789 now", ["+48123456789"]),
        ("No phone number here", []),
        ("number: +1 ", []),
        (
            "Jan Kowalski Python Developer Number: +48 123 456 789 Email: jan@example.com ",
            ["+48123456789"],
        ),
    ],
)
def test_extract_phone(input_text: str, expected_phone: list[str]) -> None:
    assert extract_phones(input_text) == expected_phone
