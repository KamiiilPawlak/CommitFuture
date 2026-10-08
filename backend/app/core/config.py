from dataclasses import dataclass
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]
STORAGE_DIR = BASE_DIR / "storage" / "cv_uploads"


@dataclass(frozen=True)
class OCRConfig:
    MIN_TEXT_LENGTH: int = 100
    TESSERACT_LANG: str = "pol+eng"
    APPLY_SHARPEN: bool = True


class Settings(BaseSettings):
    # file and security
    MAX_FILE_SIZE: int = 5 * 1024 * 1024
    ALLOWED_MIME_TYPES: list[str] = ["application/pdf", "image/png", "image/jpeg"]

    # OCR Config
    TESSERACT_CMD: str | None = None

    # Database
    DATABASE_URL: str = Field(default=...)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
