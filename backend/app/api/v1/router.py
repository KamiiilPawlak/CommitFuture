# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.routes import health, ingestion, job_posting

api_router = APIRouter()


api_router.include_router(health.router, prefix="/health", tags=["System Health"])
api_router.include_router(ingestion.router, tags=["CV Ingestion"])
api_router.include_router(job_posting.router, tags=["Job Posting Ingestion"])
