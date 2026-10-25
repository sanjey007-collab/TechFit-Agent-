import httpx
from typing import Optional

_test_store_app = None

def set_test_store_app(app):
    global _test_store_app
    _test_store_app = app

def get_store_http_client(timeout: float = 10.0) -> httpx.AsyncClient:
    if _test_store_app is not None:
        transport = httpx.ASGITransport(app=_test_store_app)
        return httpx.AsyncClient(transport=transport, base_url="http://localhost:8001", timeout=timeout)
    return httpx.AsyncClient(timeout=timeout)
