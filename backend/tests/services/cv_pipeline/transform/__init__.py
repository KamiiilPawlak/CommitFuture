from app.services.etl_cv_service.cleaning import clean_ocr_text


def test_clean_ocr_text_remoces_noise_and_keeps_email() -> None:
    dirty_text: str = (
        "Piotr Zieli ski\nEmail: piotr.zielinski@email.com\n(cid:127) Linux"
    )

    result = clean_ocr_text(dirty_text)

    assert "piotr.zielinski@email.com" in result
    assert "(cid:127)" not in result
    assert "Linux" in result
