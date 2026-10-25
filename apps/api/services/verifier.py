import httpx
from datetime import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from ..config import settings
from ..models import CartAction, VerificationResult, CartProposal
from packages.shared_schemas.models import VerificationStatus

from ..services.store_client import get_store_http_client

async def verify_cart_state(
    action: CartAction,
    proposal: CartProposal,
    db: AsyncSession
) -> VerificationResult:
    """
    Independently queries the Mock Store API and verifies that the approved SKU
    and quantity genuinely exist in the remote cart.
    Marks VERIFIED if true, FAILED if item missing or wrong quantity.
    """
    cart_id = proposal.cart_id
    expected_sku = proposal.product_sku
    expected_qty = proposal.quantity

    headers = {
        "Authorization": f"Bearer {settings.MOCK_STORE_SERVICE_TOKEN}"
    }

    url = f"{settings.mock_store_base_url.rstrip('/')}/store/cart/{cart_id}"
    observed_sku = None
    observed_qty = 0
    verified_status = VerificationStatus.FAILED
    details = ""

    try:
        async with get_store_http_client(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                # Search for expected SKU in cart
                matched_item = next((item for item in items if item.get("sku") == expected_sku), None)
                if matched_item:
                    observed_sku = matched_item.get("sku")
                    observed_qty = matched_item.get("quantity", 0)

                    if observed_qty == expected_qty:
                        verified_status = VerificationStatus.VERIFIED
                        details = f"Cart state verified independently: remote cart contains {observed_qty}x SKU '{observed_sku}'."
                    else:
                        verified_status = VerificationStatus.FAILED
                        details = f"Quantity mismatch: expected {expected_qty}x, but remote cart has {observed_qty}x."
                else:
                    verified_status = VerificationStatus.FAILED
                    details = f"Independent verifier alert: Mock store reported success, but SKU '{expected_sku}' is NOT present in cart."
            else:
                verified_status = VerificationStatus.FAILED
                details = f"Mock store returned HTTP {resp.status_code} during independent cart verification: {resp.text[:150]}"
    except Exception as e:
        verified_status = VerificationStatus.FAILED
        details = f"Independent verifier network connection failure to Mock Store: {str(e)}"

    ver_record = VerificationResult(
        id=f"ver_{action.id}",
        action_id=action.id,
        cart_id=cart_id,
        expected_sku=expected_sku,
        expected_qty=expected_qty,
        observed_sku=observed_sku,
        observed_qty=observed_qty,
        status=verified_status.value,
        verified_at=datetime.utcnow(),
        details=details
    )
    db.add(ver_record)
    await db.commit()
    await db.refresh(ver_record)

    return ver_record
