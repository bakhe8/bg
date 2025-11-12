"""
Simple health endpoint for the refactor API.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}


__all__ = ["router"]
