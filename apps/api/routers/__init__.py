from .health import router as health_router
from .admin import router as admin_router
from .checks import router as checks_router
from .products import router as products_router
from .cart import router as cart_router
from .tests_runner import router as tests_runner_router

__all__ = [
    "health_router",
    "admin_router",
    "checks_router",
    "products_router",
    "cart_router",
    "tests_runner_router",
]
