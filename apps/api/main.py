import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .seed import seed_backend
from .routers import health, admin, checks, products, cart, tests_runner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("techfit.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TechFit Agent API...")
    await seed_backend()
    logger.info("Database migration & seed ready.")
    yield
    logger.info("Shutting down TechFit Agent API.")

app = FastAPI(
    title="TechFit Agent API — AI-Powered Product Compatibility Checker",
    version="1.0.0",
    description="Deterministic rule engines, agentic retrieval, independent cart verification, and audit trail.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
origins = settings.cors_origin_list
if "*" in origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=r"https://.*\.onrender\.com|http://localhost:\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Routers
app.include_router(health.router)
app.include_router(admin.router)
app.include_router(checks.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(tests_runner.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.main:app", host=settings.HOST, port=settings.PORT, reload=True)
