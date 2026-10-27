import time
import uuid
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from ..database import get_db
from ..models import TestRun
from ..config import settings
from ..services.store_client import get_store_http_client, get_internal_store_client
from .checks import create_check, clarify_check
from .cart import approve_cart_proposal
from packages.shared_schemas.models import (
    CheckRequest, ClarifyRequest, CartApprovalRequest, TestRunItem,
    TestRunSummary, PartType, RamPreferences, ChargerPreferences
)

router = APIRouter(prefix="/api/tests", tags=["Official Test Dashboard"])

async def _reset_store_cart(cart_id: str):
    """Utility to clear cart before test run."""
    url = f"{settings.mock_store_base_url.rstrip('/')}/store/cart/{cart_id}"
    headers = {"Authorization": f"Bearer {settings.MOCK_STORE_SERVICE_TOKEN}"}
    try:
        resp = None
        try:
            async with get_store_http_client(timeout=5.0) as client:
                resp = await client.delete(url, headers=headers)
        except Exception:
            pass
        if resp is None or resp.status_code in (502, 503, 504):
            internal_url = f"http://mock-store-internal/store/cart/{cart_id}"
            async with get_internal_store_client(timeout=5.0) as client:
                await client.delete(internal_url, headers=headers)
    except Exception:
        pass

async def _get_cart_item_count(cart_id: str) -> int:
    url = f"{settings.mock_store_base_url.rstrip('/')}/store/cart/{cart_id}"
    headers = {"Authorization": f"Bearer {settings.MOCK_STORE_SERVICE_TOKEN}"}
    try:
        resp = None
        try:
            async with get_store_http_client(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)
        except Exception:
            pass
        if resp is None or resp.status_code in (502, 503, 504):
            internal_url = f"http://mock-store-internal/store/cart/{cart_id}"
            async with get_internal_store_client(timeout=5.0) as client:
                resp = await client.get(internal_url, headers=headers)
        if resp is not None and resp.status_code == 200:
            return resp.json().get("item_count", 0)
    except Exception:
        pass
    return 0

@router.post("/run", response_model=TestRunSummary)
async def run_official_tests(db: AsyncSession = Depends(get_db)):
    results: List[TestRunItem] = []
    start_all = time.time()

    # -------------------------------------------------------------
    # TC1: DDR4 Laptop [S20]
    # Input: DEMO-LAPTOP-001, part RAM, 16GB
    # Expected: COMPATIBLE, selects RAM-A, cart untouched before approval,
    #           RAM-A added once after approval, status VERIFIED.
    # -------------------------------------------------------------
    t1_start = time.time()
    t1_logs = []
    t1_cart_id = f"test-cart-tc1-{uuid.uuid4().hex[:6]}"
    await _reset_store_cart(t1_cart_id)

    t1_logs.append(f"TC1 initial cart item count: {await _get_cart_item_count(t1_cart_id)}")
    tc1_req = CheckRequest(
        device_brand="DemoTech",
        device_model="DEMO-LAPTOP-001",
        part_type=PartType.RAM,
        ram_preferences=RamPreferences(requested_capacity_gb=16),
        cart_id=t1_cart_id
    )
    report_tc1 = await create_check(tc1_req, db)
    t1_logs.append(f"Analysis complete: Verdict={report_tc1.verdict.value}, Recommended SKU={report_tc1.recommended_sku}")

    cart_count_before = await _get_cart_item_count(t1_cart_id)
    t1_logs.append(f"Cart count BEFORE approval: {cart_count_before} (assert == 0)")

    # Execute Approval
    proposal = report_tc1.proposal
    approval_status = "NOT_PROPOSED"
    verification_status = "NOT_VERIFIED"
    if proposal:
        idemp_key = f"tc1-idemp-{uuid.uuid4().hex[:8]}"
        appr_req = CartApprovalRequest(
            proposal_id=proposal.proposal_id,
            check_id=report_tc1.check_id,
            product_sku=proposal.product_sku,
            proposal_version=proposal.version,
            idempotency_key=idemp_key
        )
        appr_res = await approve_cart_proposal(proposal.proposal_id, appr_req, db)
        approval_status = appr_res.status.value
        t1_logs.append(f"Approval executed: status={approval_status}")

        # Test duplicate idempotency retry
        dup_res = await approve_cart_proposal(proposal.proposal_id, appr_req, db)
        t1_logs.append(f"Duplicate approval retry: {dup_res.message}")

    cart_count_after = await _get_cart_item_count(t1_cart_id)
    t1_logs.append(f"Cart count AFTER approval: {cart_count_after} (assert == 1)")

    tc1_pass = (
        report_tc1.verdict.value == "COMPATIBLE" and
        report_tc1.recommended_sku == "RAM-A" and
        cart_count_before == 0 and
        cart_count_after == 1 and
        approval_status == "EXECUTED"
    )
    t1_duration = round((time.time() - t1_start) * 1000, 2)

    results.append(TestRunItem(
        test_case_id="TC1",
        test_name="Official TC1 — DDR4 Laptop",
        input_summary="DEMO-LAPTOP-001, RAM upgrade 16GB",
        expected_verdict="COMPATIBLE",
        actual_verdict=report_tc1.verdict.value,
        expected_cart_status="Cart unchanged before approval; RAM-A added exactly once after approval (VERIFIED)",
        actual_cart_status=f"Before: {cart_count_before} items | After: {cart_count_after} items (SKU: RAM-A)",
        pass_fail="PASS" if tc1_pass else "FAIL",
        logs=t1_logs,
        duration_ms=t1_duration
    ))

    # -------------------------------------------------------------
    # TC2: Conflicting Sources [S21]
    # Input: DEMO-LAPTOP-002, request 16GB RAM
    # Expected: UNCERTAIN, cart must remain unchanged
    # -------------------------------------------------------------
    t2_start = time.time()
    t2_logs = []
    t2_cart_id = f"test-cart-tc2-{uuid.uuid4().hex[:6]}"
    await _reset_store_cart(t2_cart_id)

    tc2_req = CheckRequest(
        device_brand="DemoTech",
        device_model="DEMO-LAPTOP-002",
        part_type=PartType.RAM,
        ram_preferences=RamPreferences(requested_capacity_gb=16),
        cart_id=t2_cart_id
    )
    report_tc2 = await create_check(tc2_req, db)
    t2_logs.append(f"Analysis complete: Verdict={report_tc2.verdict.value}")
    t2_logs.append(f"Verdict summary: {report_tc2.verdict_summary}")
    t2_logs.append(f"Proposal present: {report_tc2.proposal is not None}")

    cart_count_tc2 = await _get_cart_item_count(t2_cart_id)
    t2_logs.append(f"Cart count: {cart_count_tc2} (assert == 0)")

    tc2_pass = (
        report_tc2.verdict.value == "UNCERTAIN" and
        report_tc2.proposal is None and
        cart_count_tc2 == 0
    )
    t2_duration = round((time.time() - t2_start) * 1000, 2)

    results.append(TestRunItem(
        test_case_id="TC2",
        test_name="Official TC2 — Conflicting Sources",
        input_summary="DEMO-LAPTOP-002, 16GB RAM (DDR4 PSREF vs DDR5 Bulletin)",
        expected_verdict="UNCERTAIN",
        actual_verdict=report_tc2.verdict.value,
        expected_cart_status="Cart unchanged (Proposal blocked)",
        actual_cart_status=f"Cart has {cart_count_tc2} items (Blocked)",
        pass_fail="PASS" if tc2_pass else "FAIL",
        logs=t2_logs,
        duration_ms=t2_duration
    ))

    # -------------------------------------------------------------
    # TC3: Unknown Model [S22]
    # Input: 'Dell laptop', request 8GB RAM
    # Expected: MORE_INFO_REQUIRED, asks for model/service tag, cart unchanged
    # Also tests clarify resume path!
    # -------------------------------------------------------------
    t3_start = time.time()
    t3_logs = []
    t3_cart_id = f"test-cart-tc3-{uuid.uuid4().hex[:6]}"
    await _reset_store_cart(t3_cart_id)

    tc3_req = CheckRequest(
        device_brand="Dell",
        device_model="Dell laptop",
        part_type=PartType.RAM,
        ram_preferences=RamPreferences(requested_capacity_gb=8),
        cart_id=t3_cart_id
    )
    report_tc3 = await create_check(tc3_req, db)
    t3_logs.append(f"Initial check: Verdict={report_tc3.verdict.value}, Identity={report_tc3.identity_status.value}")
    t3_logs.append(f"Instruction prompt: {report_tc3.verdict_summary}")

    # Test clarify resume path
    clarified_report = await clarify_check(
        report_tc3.check_id,
        ClarifyRequest(clarified_model="DEMO-LAPTOP-001"),
        db
    )
    t3_logs.append(f"Resumed check after clarification to 'DEMO-LAPTOP-001': Verdict={clarified_report.verdict.value}")

    cart_count_tc3 = await _get_cart_item_count(t3_cart_id)
    t3_logs.append(f"Cart count: {cart_count_tc3} (assert == 0)")

    tc3_pass = (
        report_tc3.verdict.value == "MORE_INFO_REQUIRED" and
        report_tc3.proposal is None and
        clarified_report.verdict.value == "COMPATIBLE" and
        cart_count_tc3 == 0
    )
    t3_duration = round((time.time() - t3_start) * 1000, 2)

    results.append(TestRunItem(
        test_case_id="TC3",
        test_name="Official TC3 — Unknown / Ambiguous Model",
        input_summary="'Dell laptop', 8GB RAM -> Clarified to 'DEMO-LAPTOP-001'",
        expected_verdict="MORE_INFO_REQUIRED",
        actual_verdict=report_tc3.verdict.value,
        expected_cart_status="Cart unchanged; resumes cleanly on clarification",
        actual_cart_status=f"Cart has {cart_count_tc3} items; Resume: {clarified_report.verdict.value}",
        pass_fail="PASS" if tc3_pass else "FAIL",
        logs=t3_logs,
        duration_ms=t3_duration
    ))

    # -------------------------------------------------------------
    # TC4: Unsupported Universal Claim [S23]
    # Input: DEMO-LAPTOP-004, candidate UNIVERSAL-CHARGER-001
    # Expected: NOT_TRUSTED, cart blocked
    # -------------------------------------------------------------
    t4_start = time.time()
    t4_logs = []
    t4_cart_id = f"test-cart-tc4-{uuid.uuid4().hex[:6]}"
    await _reset_store_cart(t4_cart_id)

    tc4_req = CheckRequest(
        device_brand="DemoTech",
        device_model="DEMO-LAPTOP-004",
        part_type=PartType.CHARGER,
        candidate_sku="UNIVERSAL-CHARGER-001",
        cart_id=t4_cart_id
    )
    report_tc4 = await create_check(tc4_req, db)
    t4_logs.append(f"Analysis complete: Verdict={report_tc4.verdict.value}")
    t4_logs.append(f"Verdict summary: {report_tc4.verdict_summary}")

    cart_count_tc4 = await _get_cart_item_count(t4_cart_id)
    t4_logs.append(f"Cart count: {cart_count_tc4} (assert == 0)")

    tc4_pass = (
        report_tc4.verdict.value == "NOT_TRUSTED" and
        report_tc4.proposal is None and
        cart_count_tc4 == 0
    )
    t4_duration = round((time.time() - t4_start) * 1000, 2)

    results.append(TestRunItem(
        test_case_id="TC4",
        test_name="Official TC4 — Unsupported Universal Claim",
        input_summary="DEMO-LAPTOP-004 + UNIVERSAL-CHARGER-001 (unverified universal fit)",
        expected_verdict="NOT_TRUSTED",
        actual_verdict=report_tc4.verdict.value,
        expected_cart_status="Cart unchanged (Proposal blocked)",
        actual_cart_status=f"Cart has {cart_count_tc4} items (Blocked)",
        pass_fail="PASS" if tc4_pass else "FAIL",
        logs=t4_logs,
        duration_ms=t4_duration
    ))

    # Persist test runs to DB
    for r in results:
        tr = TestRun(
            id=f"tr_{uuid.uuid4().hex[:12]}",
            test_case_id=r.test_case_id,
            test_name=r.test_name,
            expected_verdict=r.expected_verdict,
            actual_verdict=r.actual_verdict,
            expected_cart_status=r.expected_cart_status,
            actual_cart_status=r.actual_cart_status,
            pass_fail=r.pass_fail,
            logs_json=json.dumps(r.logs),
            duration_ms=r.duration_ms,
            executed_at=datetime.utcnow()
        )
        db.add(tr)
    await db.commit()

    passed_count = sum(1 for r in results if r.pass_fail == "PASS")
    total_count = len(results)

    return TestRunSummary(
        total_tests=total_count,
        passed_tests=passed_count,
        failed_tests=total_count - passed_count,
        overall_status="ALL_PASSED" if passed_count == total_count else "FAILURES_DETECTED",
        executed_at=datetime.utcnow().isoformat(),
        test_results=results
    )
