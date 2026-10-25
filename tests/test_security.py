import pytest
import uuid
from apps.api.config import settings

@pytest.mark.asyncio
async def test_security_prevent_altered_approved_sku(api_client):
    # Create valid check and proposal for DEMO-LAPTOP-001 (RAM-A)
    req = {
        "device_brand": "DemoTech",
        "device_model": "DEMO-LAPTOP-001",
        "part_type": "RAM",
        "ram_preferences": {"requested_capacity_gb": 16}
    }
    resp = await api_client.post("/api/checks", json=req)
    assert resp.status_code == 200
    report = resp.json()
    proposal = report["proposal"]

    # Attacker attempts to approve RAM-B (DDR5) instead of the proposed RAM-A!
    tampered_approval = {
        "proposal_id": proposal["proposal_id"],
        "check_id": report["check_id"],
        "product_sku": "RAM-B", # TAMPERED SKU!
        "proposal_version": proposal["version"],
        "idempotency_key": f"tamper-{uuid.uuid4().hex[:8]}"
    }
    appr_resp = await api_client.post(
        f"/api/cart/proposals/{proposal['proposal_id']}/approve",
        json=tampered_approval
    )
    assert appr_resp.status_code == 400
    assert "Tampering detected" in appr_resp.json()["detail"]

@pytest.mark.asyncio
async def test_security_prevent_cart_mutation_for_incompatible_product(api_client):
    # Attempt to create proposal directly for incompatible RAM-B on DEMO-LAPTOP-001
    bad_proposal_req = {
        "check_id": "non-existent-check",
        "product_sku": "RAM-B",
        "quantity": 1,
        "rationale": "Forced proposal"
    }
    resp = await api_client.post("/api/cart/proposals", json=bad_proposal_req)
    assert resp.status_code in (400, 404)

@pytest.mark.asyncio
async def test_security_no_secret_leaks_in_responses(api_client):
    # Check all public endpoints to guarantee raw secrets never leak
    endpoints = ["/healthz", "/api/products", "/api/admin/config-status"]
    raw_keys = [settings.GEMINI_API_KEY, settings.SEARCH_API_KEY, settings.PRODUCT_DETAILS_API_KEY]
    
    for ep in endpoints:
        resp = await api_client.get(ep)
        body = resp.text
        for k in raw_keys:
            if k and len(k) > 10:
                assert k not in body, f"Security Violation: Secret leaked in {ep}!"
