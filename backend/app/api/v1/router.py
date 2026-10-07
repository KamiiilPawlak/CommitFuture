# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.routes import health, ingestion

api_router = APIRouter()


api_router.include_router(health.router, prefix="/health", tags=["System Health"])
api_router.include_router(ingestion.router, tags=["CV Ingestion"])
