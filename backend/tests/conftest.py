import os
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.core.config import settings
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


pytestmark = pytest.mark.asyncio

engine = create_engine(settings.DATABASE_URL, echo=False)


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None, None, None]:
    from app.models.cv_document import CVDocumentLake
    from app.models.cv_raw_text import CVRawText

    _ = [CVDocumentLake, CVRawText]

    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_file_service() -> MagicMock:
    service = MagicMock()
    service.save_upload_file = AsyncMock(return_value="mocked_path/cv.pdf")
    return service


@pytest.fixture
def mock_ocr_service() -> MagicMock:
    service = MagicMock()
    service.process_document = AsyncMock(
        return_value=("Sztucznie odczytany tekst z CV Kamila", 1)
    )
    return service
