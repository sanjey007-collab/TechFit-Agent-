import pytest
import uuid
from packages.shared_schemas.models import CheckRequest, ClarifyRequest, CartApprovalRequest, PartType, RamPreferences

@pytest.mark.asyncio
async def test_tc1_ddr4_laptop_e2e(api_client, store_client):
    cart_id = f"tc1-test-{uuid.uuid4().hex[:6]}"

    # Step 1: Create compatibility check
    req = {
        "device_brand": "DemoTech",
        "device_model": "DEMO-LAPTOP-001",
        "part_type": "RAM",
        "ram_preferences": {"requested_capacity_gb": 16},
        "cart_id": cart_id
    }
    resp = await api_client.post("/api/checks", json=req)
    assert resp.status_code == 200
    report = resp.json()
    assert report["verdict"] == "COMPATIBLE"
    assert report["recommended_sku"] == "RAM-A"
    assert report["proposal"] is not None
    proposal = report["proposal"]

    # Step 2: Verify cart is UNCHANGED before approval
    headers = {"Authorization": "Bearer techfit_sec_token_a984b2c1f0e478d1"}
    cart_resp = await store_client.get(f"/store/cart/{cart_id}", headers=headers)
    assert cart_resp.status_code == 200
    assert cart_resp.json()["item_count"] == 0, "Cart must remain unchanged before human approval!"

    # Step 3: Explicit Human Approval
    idemp_key = f"idemp-tc1-{uuid.uuid4().hex[:8]}"
    appr_payload = {
        "proposal_id": proposal["proposal_id"],
        "check_id": report["check_id"],
        "product_sku": proposal["product_sku"],
        "proposal_version": proposal["version"],
        "idempotency_key": idemp_key
    }
    appr_resp = await api_client.post(f"/api/cart/proposals/{proposal['proposal_id']}/approve", json=appr_payload)
    assert appr_resp.status_code == 200
    appr_data = appr_resp.json()
    assert appr_data["status"] == "EXECUTED"

    # Step 4: Verify cart contains RAM-A exactly once
    cart_resp2 = await store_client.get(f"/store/cart/{cart_id}", headers=headers)
    assert cart_resp2.status_code == 200
    cart_data2 = cart_resp2.json()
    assert cart_data2["item_count"] == 1
    assert cart_data2["items"][0]["sku"] == "RAM-A"

    # Step 5: Duplicate approval retry must not add duplicate item
    dup_resp = await api_client.post(f"/api/cart/proposals/{proposal['proposal_id']}/approve", json=appr_payload)
    assert dup_resp.status_code == 200
    cart_resp3 = await store_client.get(f"/store/cart/{cart_id}", headers=headers)
    assert cart_resp3.json()["item_count"] == 1, "Duplicate approval retry must be idempotent!"

@pytest.mark.asyncio
async def test_tc2_conflicting_sources(api_client, store_client):
    cart_id = f"tc2-test-{uuid.uuid4().hex[:6]}"
    req = {
        "device_brand": "DemoTech",
        "device_model": "DEMO-LAPTOP-002",
        "part_type": "RAM",
        "ram_preferences": {"requested_capacity_gb": 16},
        "cart_id": cart_id
    }
    resp = await api_client.post("/api/checks", json=req)
    assert resp.status_code == 200
    report = resp.json()
    assert report["verdict"] == "UNCERTAIN"
    assert "Contradictory Manufacturer Claims" in report["verdict_summary"]
    assert report["proposal"] is None, "Uncertain verdict must never create an approved cart proposal!"

    # Verify cart is unchanged
    headers = {"Authorization": "Bearer techfit_sec_token_a984b2c1f0e478d1"}
    cart_resp = await store_client.get(f"/store/cart/{cart_id}", headers=headers)
    assert cart_resp.json()["item_count"] == 0

@pytest.mark.asyncio
async def test_tc3_unknown_model_and_resume(api_client, store_client):
    cart_id = f"tc3-test-{uuid.uuid4().hex[:6]}"
    req = {
        "device_brand": "Dell",
        "device_model": "Dell laptop",
        "part_type": "RAM",
        "ram_preferences": {"requested_capacity_gb": 8},
        "cart_id": cart_id
    }
    resp = await api_client.post("/api/checks", json=req)
    assert resp.status_code == 200
    report = resp.json()
    assert report["verdict"] == "MORE_INFO_REQUIRED"
    assert report["identity_status"] == "AMBIGUOUS"
    assert report["proposal"] is None

    # Test clarification resume path
    clarify_payload = {"clarified_model": "DEMO-LAPTOP-001"}
    resume_resp = await api_client.post(f"/api/checks/{report['check_id']}/clarify", json=clarify_payload)
    assert resume_resp.status_code == 200
    resumed_report = resume_resp.json()
    assert resumed_report["verdict"] == "COMPATIBLE"
    assert resumed_report["recommended_sku"] == "RAM-A"

@pytest.mark.asyncio
async def test_tc4_unsupported_universal_claim(api_client, store_client):
    cart_id = f"tc4-test-{uuid.uuid4().hex[:6]}"
    req = {
        "device_brand": "DemoTech",
        "device_model": "DEMO-LAPTOP-004",
        "part_type": "CHARGER",
        "candidate_sku": "UNIVERSAL-CHARGER-001",
        "cart_id": cart_id
    }
    resp = await api_client.post("/api/checks", json=req)
    assert resp.status_code == 200
    report = resp.json()
    assert report["verdict"] == "NOT_TRUSTED"
    assert report["proposal"] is None, "Not trusted candidates must never create a cart proposal!"

    # Verify cart is unchanged
    headers = {"Authorization": "Bearer techfit_sec_token_a984b2c1f0e478d1"}
    cart_resp = await store_client.get(f"/store/cart/{cart_id}", headers=headers)
    assert cart_resp.json()["item_count"] == 0
