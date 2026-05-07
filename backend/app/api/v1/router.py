from fastapi import APIRouter
from .audit import router as audit_router

# Main API v1 router
api_router = APIRouter(prefix="/v1")

# Include all feature routers
api_router.include_router(audit_router, prefix="/accessibility", tags=["Accessibility"])
