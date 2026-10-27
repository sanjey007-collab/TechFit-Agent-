import httpx
import logging
from typing import Optional
from apps.mock_store.main import app as mock_store_app

logger = logging.getLogger("techfit.store_client")

_test_store_app = None

def set_test_store_app(app):
    global _test_store_app
    _test_store_app = app

def get_internal_store_client(timeout: float = 10.0) -> httpx.AsyncClient:
    app_to_use = _test_store_app if _test_store_app is not None else mock_store_app
    transport = httpx.ASGITransport(app=app_to_use)
    return httpx.AsyncClient(transport=transport, base_url="http://mock-store-internal", timeout=timeout)

def get_store_http_client(timeout: float = 10.0) -> httpx.AsyncClient:
    if _test_store_app is not None:
        return get_internal_store_client(timeout=timeout)
    
    from ..config import settings
    url = settings.MOCK_STORE_URL.strip() if settings.MOCK_STORE_URL else ""
    if not url or "localhost" in url or "127.0.0.1" in url:
        return get_internal_store_client(timeout=timeout)

    return httpx.AsyncClient(timeout=timeout)
