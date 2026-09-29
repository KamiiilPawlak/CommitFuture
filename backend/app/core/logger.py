# ai_matcher/core/logger.py
import os
import sys

from loguru import logger


def setup_logging() -> None:
    logger.remove()

    env: str = os.getenv("APP_ENV", "dev").lower()

    log_level: str = os.getenv("LOG_LEVEL", "DEBUG" if env == "dev" else "INFO").upper()

    if env in {"prod", "ci"}:
        logger.add(
            sys.stdout,
            level=log_level,
            serialize=True,
        )
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

        logger.add(sys.stdout, level=log_level, format=log_format, colorize=True)

        logger.add(
            "logs/errors.log",
            level="ERROR",
            format=log_format,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
