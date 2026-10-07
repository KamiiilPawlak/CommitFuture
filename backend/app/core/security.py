import magic
from loguru import logger

from app.core.config import settings


def verify_file_integrity(content: bytes) -> str:
    if not content:
        logger.error("Plik jest pusty")
        msg = "Przesłany plik jest pusty "
        raise ValueError(msg)

    mime_type: str = str(magic.from_buffer(content[:2024], mime=True))

    if mime_type not in settings.ALLOWED_MIME_TYPES:
        logger.error(
            f"Nieautoryzyowany format ppliku: {mime_type}"
            f"Dozwolone typy: {settings.ALLOWED_MIME_TYPES}"
        )
        msg_0 = f"Niedozwolony format {mime_type}. Akceptowane są wyłącznie pliki PDF oraz obraz"
        raise ValueError(msg_0)

    logger.info(f"Plik zerwyfikowany pomyslenie. Wykryty typ MIME {mime_type} ")
    return mime_type
