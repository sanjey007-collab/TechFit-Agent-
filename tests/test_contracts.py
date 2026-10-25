import pytest

@pytest.mark.asyncio
async def test_healthz_endpoint(api_client):
    resp = await api_client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["service"] == "techfit-api"

@pytest.mark.asyncio
async def test_admin_config_status_endpoint(api_client):
    resp = await api_client.get("/api/admin/config-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert "gemini" in data["keys"]
    assert "search" in data["keys"]
    assert "product_details" in data["keys"]
    # Never expose raw secret
    assert "AQ.Ab8RN6L" not in str(data)

@pytest.mark.asyncio
async def test_products_endpoint(api_client):
    resp = await api_client.get("/api/products")
    assert resp.status_code == 200
    prods = resp.json()
    assert len(prods) >= 4

@pytest.mark.asyncio
async def test_test_dashboard_runner_endpoint(api_client):
    resp = await api_client.post("/api/tests/run")
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["total_tests"] == 4
    assert summary["passed_tests"] == 4
    assert summary["overall_status"] == "ALL_PASSED"
