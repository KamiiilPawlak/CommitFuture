from collections.abc import Generator

from loguru import logger
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.models.cv_document import CVDocumentLake
from app.models.cv_raw_text import CVRawText
from app.models.cv_structured_data import CVStructuredData

engine = create_engine(settings.DATABASE_URL, echo=True)


def init_db() -> None:
    logger.info("Inicjalizacja bazy danych")
    _ = [CVDocumentLake, CVRawText, CVStructuredData]
    logger.success("Tabela bazy danych zostala pomyslnie utworzona")
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
