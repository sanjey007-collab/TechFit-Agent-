import json
import uuid
import httpx
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models import CartProposal, Approval, CartAction, VerificationResult, Check, Product
from ..services.verifier import verify_cart_state
from ..services.store_client import get_store_http_client
from packages.shared_schemas.models import (
    CartProposalCreate, CartProposalResponse, CartApprovalRequest,
    CartApprovalResponse, ProposalStatus, ActionStatus, CartVerificationResponse,
    VerificationStatus
)

router = APIRouter(prefix="/api/cart", tags=["Cart & Approval"])

@router.post("/proposals", response_model=CartProposalResponse)
async def create_proposal(
    req: CartProposalCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verify check exists and is COMPATIBLE
    check_stmt = select(Check).where(Check.id == req.check_id)
    check_res = await db.execute(check_stmt)
    check = check_res.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail=f"Check '{req.check_id}' not found")
    if check.verdict != "COMPATIBLE":
        raise HTTPException(
            status_code=400,
            detail=f"Cart proposal can only be created for COMPATIBLE checks. Current verdict is '{check.verdict}'."
        )

    # Fetch product
    prod_stmt = select(Product).where(Product.sku == req.product_sku)
    prod_res = await db.execute(prod_stmt)
    product = prod_res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product SKU '{req.product_sku}' not found")

    proposal_id = f"prop_{uuid.uuid4().hex[:12]}"
    proposal = CartProposal(
        id=proposal_id,
        check_id=req.check_id,
        product_sku=req.product_sku,
        quantity=req.quantity,
        cart_id=req.cart_id,
        rationale=req.rationale,
        version=1,
        status="AWAITING_APPROVAL",
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)

    return CartProposalResponse(
        proposal_id=proposal.id,
        check_id=proposal.check_id,
        product_sku=proposal.product_sku,
        product_name=product.name,
        quantity=proposal.quantity,
        price=product.price,
        cart_id=proposal.cart_id,
        rationale=proposal.rationale,
        version=proposal.version,
        status=ProposalStatus(proposal.status),
        expires_at=proposal.expires_at.isoformat(),
        created_at=proposal.created_at.isoformat()
    )

@router.post("/proposals/{proposal_id}/approve", response_model=CartApprovalResponse)
async def approve_cart_proposal(
    proposal_id: str,
    req: CartApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch proposal
    stmt = select(CartProposal).where(CartProposal.id == proposal_id)
    res = await db.execute(stmt)
    proposal = res.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found")

    # 2. Check Idempotency Key
    appr_stmt = select(Approval).where(Approval.idempotency_key == req.idempotency_key)
    appr_res = await db.execute(appr_stmt)
    existing_appr = appr_res.scalar_one_or_none()
    if existing_appr:
        # Idempotent replay: return cached execution result without modifying cart again
        return CartApprovalResponse(
            action_id=f"act_cached_{existing_appr.id}",
            proposal_id=proposal.id,
            status=ActionStatus.EXECUTED,
            executed_at=existing_appr.approved_at.isoformat(),
            message="Idempotent approval request: item was already added to cart. Duplicate mutation prevented."
        )

    # 3. Security checks
    if proposal.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Proposal cannot be approved in its current state '{proposal.status}'."
        )

    if datetime.utcnow() > proposal.expires_at:
        proposal.status = "EXPIRED"
        await db.commit()
        raise HTTPException(status_code=400, detail="Proposal has expired. A new check must be performed.")

    if req.proposal_version != proposal.version:
        raise HTTPException(
            status_code=409,
            detail=f"Proposal version conflict: expected version {proposal.version}, got {req.proposal_version}."
        )

    if req.product_sku != proposal.product_sku:
        raise HTTPException(
            status_code=400,
            detail=f"Tampering detected: approved SKU '{req.product_sku}' does not match proposed SKU '{proposal.product_sku}'."
        )

    # 4. Record human approval
    approval = Approval(
        id=f"appr_{uuid.uuid4().hex[:12]}",
        proposal_id=proposal.id,
        user_identifier="human_operator",
        approval_token=uuid.uuid4().hex,
        idempotency_key=req.idempotency_key,
        approved_at=datetime.utcnow()
    )
    db.add(approval)

    # 5. Execute Mutation on Mock Store API
    action_id = f"act_{uuid.uuid4().hex[:12]}"
    action = CartAction(
        id=action_id,
        proposal_id=proposal.id,
        action_type="ADD_ITEM",
        status="PENDING",
        request_payload_json=json.dumps({
            "sku": proposal.product_sku,
            "quantity": proposal.quantity,
            "cart_id": proposal.cart_id,
            "idempotency_key": req.idempotency_key
        })
    )
    db.add(action)
    await db.flush()

    store_url = f"{settings.mock_store_base_url.rstrip('/')}/store/cart/{proposal.cart_id}/items"
    headers = {
        "Authorization": f"Bearer {settings.MOCK_STORE_SERVICE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "sku": proposal.product_sku,
        "quantity": proposal.quantity,
        "idempotency_key": req.idempotency_key
    }

    try:
        async with get_store_http_client(timeout=10.0) as client:
            resp = await client.post(store_url, json=payload, headers=headers)
            action.response_payload_json = resp.text
            if resp.status_code == 200:
                action.status = "EXECUTED"
                proposal.status = "EXECUTED"
            else:
                action.status = "FAILED"
                proposal.status = "REJECTED"
    except Exception as e:
        action.status = "FAILED"
        action.response_payload_json = json.dumps({"error": str(e)})

    await db.commit()

    # 6. Independent Agentic Verification [S19]
    # Re-read the cart independently and confirm expected SKU and quantity
    verification = await verify_cart_state(action, proposal, db)

    if verification.status != "VERIFIED":
        action.status = "FAILED"
        await db.commit()
        return CartApprovalResponse(
            action_id=action.id,
            proposal_id=proposal.id,
            status=ActionStatus.FAILED,
            executed_at=action.executed_at.isoformat(),
            message=f"Cart execution failed independent verification: {verification.details}"
        )

    return CartApprovalResponse(
        action_id=action.id,
        proposal_id=proposal.id,
        status=ActionStatus.EXECUTED,
        executed_at=action.executed_at.isoformat(),
        message=f"Item {proposal.product_sku} added to cart and verified successfully."
    )

@router.get("/{cart_id}")
async def get_cart_state(cart_id: str):
    """
    Independently reads current live cart state from the Mock Store.
    """
    store_url = f"{settings.mock_store_base_url.rstrip('/')}/store/cart/{cart_id}"
    headers = {
        "Authorization": f"Bearer {settings.MOCK_STORE_SERVICE_TOKEN}"
    }
    try:
        async with get_store_http_client(timeout=10.0) as client:
            resp = await client.get(store_url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Cannot reach mock store: {str(e)}")
