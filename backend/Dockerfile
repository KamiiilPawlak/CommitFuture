# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# 1. Ustawienia środowiskowe Pythona
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code


RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-pol \
    libmagic1 \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml .


RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system .

COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Stage z zależnościami dev (ruff/mypy/pytest/...) — używany tylko lokalnie/CI do testów,
# nie wchodzi do obrazu uruchamianego przez docker-compose.
FROM base AS dev

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system .[dev]
