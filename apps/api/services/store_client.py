import httpx
from typing import Optional
from apps.mock_store.main import app as mock_store_app

_test_store_app = None

def set_test_store_app(app):
    global _test_store_app
    _test_store_app = app

def get_store_http_client(timeout: float = 10.0) -> httpx.AsyncClient:
    if _test_store_app is not None:
        transport = httpx.ASGITransport(app=_test_store_app)
        return httpx.AsyncClient(transport=transport, base_url="http://localhost:8001", timeout=timeout)
    
    from ..config import settings
    url = settings.MOCK_STORE_URL.strip() if settings.MOCK_STORE_URL else ""
    if not url or "localhost" in url or "127.0.0.1" in url:
        transport = httpx.ASGITransport(app=mock_store_app)
        return httpx.AsyncClient(transport=transport, base_url="http://localhost:8001", timeout=timeout)

    return httpx.AsyncClient(timeout=timeout)
