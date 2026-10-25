from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Device, DeviceVariant
from packages.shared_schemas.models import DeviceIdentityStatus

GENERIC_TERMS = {
    "laptop", "notebook", "computer", "pc", "dell laptop", "lenovo laptop", "hp laptop", "asus laptop", "acer laptop"
}

async def resolve_device_identity(
    brand: Optional[str],
    model_str: str,
    db: AsyncSession
) -> Tuple[DeviceIdentityStatus, Optional[Device], Optional[DeviceVariant], str]:
    """
    Resolves user-supplied input into an exact verified hardware device & variant.
    Returns: (status, device, variant, explanation_message)
    """
    clean_model = model_str.strip()
    clean_brand = brand.strip() if brand else ""

    # Check for empty or generic search
    if not clean_model:
        return (
            DeviceIdentityStatus.INSUFFICIENT_INPUT,
            None,
            None,
            "Please provide a device model name or number to begin compatibility analysis."
        )

    # Check if input is a generic family name (e.g. 'Dell laptop', 'Lenovo ThinkPad')
    if clean_model.lower() in GENERIC_TERMS or (clean_brand.lower() == "dell" and clean_model.lower() in ("laptop", "notebook")):
        return (
            DeviceIdentityStatus.AMBIGUOUS,
            None,
            None,
            "A broad family name like 'Dell laptop' is not a unique hardware identifier. Multiple hardware generations use different memory and charger specs. Please specify your exact model number (e.g., Inspiron 15 3520, Latitude 5420) or 7-character Dell Service Tag (found on the chassis bottom sticker, in BIOS via F2, or Dell SupportAssist)."
        )

    # Query database for exact match on model_family
    stmt = select(Device).where(Device.model_family.ilike(f"%{clean_model}%"))
    res = await db.execute(stmt)
    devices = res.scalars().all()

    if not devices and clean_brand:
        # Try combined search
        stmt2 = select(Device).where(
            Device.brand.ilike(f"%{clean_brand}%"),
            Device.model_family.ilike(f"%{clean_model}%")
        )
        res2 = await db.execute(stmt2)
        devices = res2.scalars().all()

    if not devices:
        # Check if model string is recognizable or brand known
        return (
            DeviceIdentityStatus.NOT_FOUND,
            None,
            None,
            f"Device model '{clean_model}' could not be matched directly in manufacturer index. Retrieval will query live web sources."
        )

    if len(devices) > 1:
        device_names = [f"{d.brand} {d.model_family}" for d in devices]
        return (
            DeviceIdentityStatus.AMBIGUOUS,
            None,
            None,
            f"Multiple matching models found: {', '.join(device_names)}. Please provide the exact sub-model or serial identifier."
        )

    matched_device = devices[0]
    # Fetch primary variant
    v_stmt = select(DeviceVariant).where(DeviceVariant.device_id == matched_device.id)
    v_res = await db.execute(v_stmt)
    variants = v_res.scalars().all()

    primary_variant = variants[0] if variants else None

    return (
        DeviceIdentityStatus.RESOLVED,
        matched_device,
        primary_variant,
        f"Resolved device: {matched_device.brand} {matched_device.model_family} ({primary_variant.full_name if primary_variant else 'Default Variant'})."
    )
