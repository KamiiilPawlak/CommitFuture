import asyncio
import io

import pdfplumber
import pytesseract
from loguru import logger
from pdf2image import convert_from_bytes
from PIL import Image, ImageFilter, ImageOps

from app.core.config import OCRConfig, settings


class OCRService:
    def __init__(self) -> None:
        self._config = OCRConfig()
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    async def process_document(self, content: bytes, mime_type: str) -> tuple[str, int]:
        if mime_type == "application/pdf":
            text, page_count = self._extract_digital_text(content)
            logger.info("Proba ekstrakcji tekstu cyfrowego z pliku PDF")
            if text.strip() and len(text) > self._config.MIN_TEXT_LENGTH:
                logger.info("Pomyślnie wyekstrahowano tekst cyfrowy z PDF.")
                return text, page_count
        logger.info(f"Uruchamianie procesu OCR dla typu: {mime_type}")
        return await asyncio.to_thread(self._extract_via_ocr, content, mime_type)

    def _extract_digital_text(self, content: bytes) -> tuple[str, int]:
        full_text = []
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text.append(page_text)

                    current_length = len("\n".join(full_text).strip())
                    if current_length > self._config.MIN_TEXT_LENGTH:
                        logger.info(
                            "Przekroczono minimalny próg tekstu cyfrowego, przerywam czytanie PDF."
                        )
                        break

            return "\n".join(full_text), page_count
        except Exception as e:
            logger.error(f"Błąd podczas ekstrakcji tekstu cyfrowego: {e}")
            return "", 0

    def _extract_via_ocr(self, content: bytes, mime_type: str) -> tuple[str, int]:
        if mime_type == "application/pdf":
            images = convert_from_bytes(content)
        else:
            images = [Image.open(io.BytesIO(content))]

        results = []

        for img in images:
            processed = self._apply_pil_filters(img)
            text = pytesseract.image_to_string(
                processed, lang=self._config.TESSERACT_LANG
            )
            results.append(text)

        return "\n".join(results), len(images)

    def _apply_pil_filters(self, img: Image.Image) -> Image.Image:
        img = img.convert("L")
        img = ImageOps.autocontrast(img)
        if self._config.APPLY_SHARPEN:
            img = img.filter(ImageFilter.SHARPEN)

        return img
