from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.v1.router import api_router
from app.core.logger import setup_logging

from .db.database import init_db

setup_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Uruchomienie aplikacji")
    init_db()
    yield
    logger.info("Zamykanie aplikacji")


app = FastAPI(title="CV AI Matcher", lifespan=lifespan)


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    logger.debug("Wywolano endpoint glowny root")
    return {"message": "docker :D"}


logger.success("Aplikacja zostala pomyslnie zainicjalizowana i wystartowala")
