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

    # LLM Config
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_NAME: str = "qwen2.5:1.5b"
    OLLAMA_NUM_THREAD: int = 4
    OLLAMA_TEMPERATURE: float = 0.0
    OLLAMA_NUM_CTX: int = 2048
    OLLAMA_TIMEOUT: float = 200.0
    OLLAMA_MAX_RETRIES: int = 3
    OLLAMA_RETRY_BACKOFF_SECONDS: float = 1.0

    # Database
    DATABASE_URL: str = Field(default=...)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
