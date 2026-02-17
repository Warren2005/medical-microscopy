"""
API v1 router — combines all endpoint modules.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, search, images

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(images.router, prefix="/images", tags=["Images"])
