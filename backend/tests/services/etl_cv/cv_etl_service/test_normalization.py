import pytest

from app.services.etl_cv_service.normalization import CVTextNormalizer


@pytest.fixture
def normalizer() -> CVTextNormalizer:
    return CVTextNormalizer()


def test_normalize_punctuation(normalizer: CVTextNormalizer) -> None:

    input_text = "Doświadczenie: „Python Developer” w Firma X (05.2020 - 08.2022) — praca w trybie hybrid."
    expected = 'Doświadczenie: "Python Developer" w Firma X (2020-05 - 2022-08) - praca w trybie hybrid.'

    result = normalizer.normalize_text(input_text)
    assert result == expected


def test_normalize_dates_digits(normalizer: CVTextNormalizer) -> None:

    text1 = "Praca od 03/2019 do 12.2021"
    assert normalizer.normalize_text(text1) == "Praca od 2019-03 do 2021-12"

    text2 = "Okres: 2020/05 - 2022/08"
    assert normalizer.normalize_text(text2) == "Okres: 2020-05 - 2022-08"


def test_normalize_dates_text_and_present(normalizer: CVTextNormalizer) -> None:

    text = "Styczeń 2020 - obecnie"
    assert normalizer.normalize_text(text) == "2020-01 - PRESENT"

    text_en = "March 2021 - present"
    assert normalizer.normalize_text(text_en) == "2021-03 - PRESENT"


def test_normalize_phone_numbers(normalizer: CVTextNormalizer) -> None:

    text = "Kontakt: +48 (123) 456-789 lub 500 600 700"
    result = normalizer.normalize_text(text)
    assert "+48123456789" in result
    assert "500600700" in result


def test_normalize_language_levels(normalizer: CVTextNormalizer) -> None:

    text = "Angielski b2, Niemiecki a2"
    assert normalizer.normalize_text(text) == "Angielski B2, Niemiecki A2"


def test_normalize_hyperlinks(normalizer: CVTextNormalizer) -> None:
    text = (
        "Profil: https://www.linkedin.com/in/jan-kowalski oraz https://github.com/user"
    )
    result = normalizer.normalize_text(text)
    assert "linkedin.com/in/jan-kowalski" in result
    assert "github.com/user" in result


def test_normalize_empty_text(normalizer: CVTextNormalizer) -> None:
    assert normalizer.normalize_text("") == ""
    assert normalizer.normalize_text(None) == ""
