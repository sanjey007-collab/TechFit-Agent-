from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/healthz")
async def health_check():
    return {
        "status": "ok",
        "service": "techfit-api",
        "version": "1.0.0"
    }
