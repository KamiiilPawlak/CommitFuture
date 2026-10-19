import os
from collections.abc import Generator
from pathlib import Path

from alembic import command
from alembic.config import Config
from loguru import logger
from sqlmodel import Session, create_engine

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)

BACKEND_DIR = Path(__file__).resolve().parents[2]


def run_migrations() -> None:
    if os.getenv("SKIP_MIGRATIONS") == "1":
        logger.info("Pominięto migracje Alembic (SKIP_MIGRATIONS=1)")
        return

    logger.info("Stosowanie migracji Alembic do najnowszej wersji (head)")
    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    logger.success("Schemat bazy danych jest aktualny")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
