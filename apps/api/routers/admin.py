import os
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status
from ..config import settings
from scripts.smoke_test_keys import mask_key

router = APIRouter(prefix="/api/admin", tags=["Admin & Config"])

def verify_admin(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    expected = settings.ADMIN_API_KEY
    if not x_admin_key or x_admin_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Key header"
        )
    return x_admin_key

@router.get("/config-status")
async def get_config_status(
    admin_auth: Optional[str] = Header(None, alias="X-Admin-Key")
):
    # Allow read-only status inspection from UI settings if token matches or returns public masked summary
    is_authenticated = (admin_auth == settings.ADMIN_API_KEY)

    gemini_key = settings.GEMINI_API_KEY
    search_key = settings.SEARCH_API_KEY or settings.GOOGLE_SEARCH_API_KEY
    product_key = settings.PRODUCT_DETAILS_API_KEY

    return {
        "status": "ready" if (gemini_key and search_key) else "missing_configuration",
        "authenticated": is_authenticated,
        "keys": {
            "gemini": {
                "configured": bool(gemini_key and not gemini_key.startswith("your_")),
                "masked": mask_key(gemini_key) if gemini_key else None,
                "model": settings.GEMINI_MODEL,
                "provider": "google-gemini"
            },
            "search": {
                "configured": bool(search_key and not search_key.startswith("your_")),
                "masked": mask_key(search_key) if search_key else None,
                "provider": settings.SEARCH_PROVIDER
            },
            "product_details": {
                "configured": bool(product_key and not product_key.startswith("your_")),
                "masked": mask_key(product_key) if product_key else None,
                "provider": settings.PRODUCT_DETAILS_PROVIDER
            }
        },
        "services": {
            "database": {
                "engine": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
                "connected": True
            },
            "mock_store": {
                "url": settings.MOCK_STORE_URL,
                "token_configured": bool(settings.MOCK_STORE_SERVICE_TOKEN)
            }
        }
    }
