import pytest
import uuid
from apps.api.config import settings

@pytest.mark.asyncio
async def test_mock_store_health(store_client):
    resp = await store_client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "techfit-mock-store"

@pytest.mark.asyncio
async def test_mock_store_products_listing(store_client):
    resp = await store_client.get("/store/products")
    assert resp.status_code == 200
    products = resp.json()
    assert len(products) >= 4
    skus = [p["sku"] for p in products]
    assert "RAM-A" in skus
    assert "RAM-B" in skus
    assert "UNIVERSAL-CHARGER-001" in skus

@pytest.mark.asyncio
async def test_mock_store_token_authentication(store_client):
    cart_id = f"test-cart-{uuid.uuid4().hex[:6]}"
    # 1. Missing Authorization header -> 401
    resp_no_auth = await store_client.get(f"/store/cart/{cart_id}")
    assert resp_no_auth.status_code == 401

    # 2. Invalid token -> 401
    resp_bad_auth = await store_client.get(
        f"/store/cart/{cart_id}",
        headers={"Authorization": "Bearer invalid_secret_token"}
    )
    assert resp_bad_auth.status_code == 401

    # 3. Valid token -> 200
    resp_ok = await store_client.get(
        f"/store/cart/{cart_id}",
        headers={"Authorization": f"Bearer {settings.MOCK_STORE_SERVICE_TOKEN}"}
    )
    assert resp_ok.status_code == 200
    data = resp_ok.json()
    assert data["cart_id"] == cart_id
    assert data["item_count"] == 0

@pytest.mark.asyncio
async def test_mock_store_idempotent_cart_addition(store_client):
    cart_id = f"test-cart-{uuid.uuid4().hex[:6]}"
    headers = {"Authorization": f"Bearer {settings.MOCK_STORE_SERVICE_TOKEN}"}
    idemp_key = f"idemp-{uuid.uuid4().hex[:8]}"

    payload = {
        "sku": "RAM-A",
        "quantity": 1,
        "idempotency_key": idemp_key
    }

    # First addition
    resp1 = await store_client.post(f"/store/cart/{cart_id}/items", json=payload, headers=headers)
    assert resp1.status_code == 200
    cart1 = resp1.json()
    assert cart1["item_count"] == 1
    assert cart1["items"][0]["sku"] == "RAM-A"

    # Second addition with SAME idempotency key -> MUST NOT duplicate quantity!
    resp2 = await store_client.post(f"/store/cart/{cart_id}/items", json=payload, headers=headers)
    assert resp2.status_code == 200
    cart2 = resp2.json()
    assert cart2["item_count"] == 1, "Idempotent retry must not add duplicate items!"
