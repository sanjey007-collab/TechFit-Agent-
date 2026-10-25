import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Check, RuleResult, Device, DeviceVariant, SpecFact, Source, Product, CartProposal, VerificationResult
from ..services.identity import resolve_device_identity
from ..services.rule_engine import evaluate_ram_compatibility, evaluate_charger_compatibility
from packages.shared_schemas.models import (
    CheckRequest, ClarifyRequest, CompatibilityReport, CompatibilityVerdict,
    DeviceIdentityStatus, RuleComparison, EvidenceItem, CartProposalResponse,
    CartVerificationResponse, ProposalStatus, VerificationStatus, PartType
)

router = APIRouter(prefix="/api/checks", tags=["Compatibility Checks"])

def _format_proposal(p: Optional[CartProposal], product_name: str = "", price: float = 0.0) -> Optional[CartProposalResponse]:
    if not p:
        return None
    return CartProposalResponse(
        proposal_id=p.id,
        check_id=p.check_id,
        product_sku=p.product_sku,
        product_name=product_name or p.product_sku,
        quantity=p.quantity,
        price=price,
        cart_id=p.cart_id,
        rationale=p.rationale,
        version=p.version,
        status=ProposalStatus(p.status),
        expires_at=p.expires_at.isoformat(),
        created_at=p.created_at.isoformat()
    )

def _format_verification(v: Optional[VerificationResult]) -> Optional[CartVerificationResponse]:
    if not v:
        return None
    return CartVerificationResponse(
        verification_id=v.id,
        action_id=v.action_id,
        cart_id=v.cart_id,
        expected_sku=v.expected_sku,
        expected_qty=v.expected_qty,
        observed_sku=v.observed_sku,
        observed_qty=v.observed_qty,
        status=VerificationStatus(v.status),
        verified_at=v.verified_at.isoformat(),
        details=v.details
    )

async def _build_report(check: Check, db: AsyncSession) -> CompatibilityReport:
    # Fetch relations
    rule_stmt = select(RuleResult).where(RuleResult.check_id == check.id)
    rule_res = await db.execute(rule_stmt)
    rules = rule_res.scalars().all()

    prop_stmt = (
        select(CartProposal)
        .options(selectinload(CartProposal.actions))
        .where(CartProposal.check_id == check.id)
        .order_by(CartProposal.version.desc())
    )
    prop_res = await db.execute(prop_stmt)
    proposal = prop_res.scalars().first()

    # Find verification if proposal executed
    verification = None
    if proposal and proposal.actions:
        action = proposal.actions[-1]
        v_stmt = select(VerificationResult).where(VerificationResult.action_id == action.id)
        v_res = await db.execute(v_stmt)
        verification = v_res.scalar_one_or_none()

    # Fetch product details for proposal
    prod_name = ""
    prod_price = 0.0
    if proposal:
        prod_stmt = select(Product).where(Product.sku == proposal.product_sku)
        prod_res = await db.execute(prod_stmt)
        prod = prod_res.scalar_one_or_none()
        if prod:
            prod_name = prod.name
            prod_price = prod.price

    # Fetch evidence items
    evidence_items: List[EvidenceItem] = []
    source_ids = [r.evidence_source_id for r in rules if r.evidence_source_id]
    if source_ids:
        src_stmt = select(Source).where(Source.id.in_(source_ids))
        src_res = await db.execute(src_stmt)
        sources = src_res.scalars().all()
        for s in sources:
            evidence_items.append(EvidenceItem(
                source_id=s.id,
                url=s.url,
                title=s.title,
                domain=s.domain,
                excerpt=s.excerpt,
                retrieval_timestamp=s.retrieval_timestamp.isoformat(),
                applicability=s.applicability,
                is_official=s.is_official
            ))

    comparisons = [
        RuleComparison(
            rule_name=r.rule_name,
            field_name=r.field_name,
            required_value=r.required_value,
            observed_value=r.observed_value,
            status=r.status,
            evidence_source_id=r.evidence_source_id,
            explanation=r.explanation
        )
        for r in rules
    ]

    device_brand = ""
    device_model = ""
    if check.resolved_device_id:
        dev_res = await db.execute(select(Device).where(Device.id == check.resolved_device_id))
        dev = dev_res.scalar_one_or_none()
        if dev:
            device_brand = dev.brand
            device_model = dev.model_family
    elif check.user_input_json:
        try:
            u_in = json.loads(check.user_input_json)
            device_brand = u_in.get("device_brand", "")
            device_model = u_in.get("device_model", "")
        except Exception:
            pass

    return CompatibilityReport(
        check_id=check.id,
        request_id=check.request_id,
        identity_status=DeviceIdentityStatus(check.identity_status),
        resolved_device_brand=device_brand or check.resolved_device_id,
        resolved_device_model=device_model or check.resolved_variant_id,
        resolved_variant=check.resolved_variant_id,
        part_type=PartType(check.part_type),
        verdict=CompatibilityVerdict(check.verdict),
        verdict_summary=check.verdict_summary,
        detailed_explanation=check.detailed_explanation,
        comparisons=comparisons,
        evidence_items=evidence_items,
        recommended_sku=check.recommended_sku,
        proposal=_format_proposal(proposal, prod_name, prod_price),
        verification=_format_verification(verification),
        next_action_instructions=check.next_action_instructions,
        created_at=check.created_at.isoformat(),
        updated_at=check.updated_at.isoformat()
    )

@router.post("", response_model=CompatibilityReport)
async def create_check(req: CheckRequest, db: AsyncSession = Depends(get_db)):
    check_id = f"chk_{uuid.uuid4().hex[:12]}"
    request_id = f"req_{uuid.uuid4().hex[:8]}"

    # Step 1: Device Identity Resolution
    status_id, device, variant, id_msg = await resolve_device_identity(
        brand=req.device_brand,
        model_str=req.device_model,
        db=db
    )

    if status_id != DeviceIdentityStatus.RESOLVED:
        # Stop early with MORE_INFO_REQUIRED (e.g. TC3 Dell laptop)
        verdict = CompatibilityVerdict.MORE_INFO_REQUIRED
        summary = f"Identity Ambiguity: {id_msg}"
        explanation = (
            "The exact hardware model could not be unambiguously resolved. "
            "To prevent providing incorrect specifications or incompatible recommendations, "
            "please provide the exact model number or serial identifier."
        )
        instructions = "Please supply the exact model number using the clarification prompt below."

        check = Check(
            id=check_id,
            request_id=request_id,
            user_input_json=req.model_dump_json(),
            resolved_device_id=device.id if device else None,
            resolved_variant_id=variant.id if variant else None,
            identity_status=status_id.value,
            part_type=req.part_type.value,
            verdict=verdict.value,
            verdict_summary=summary,
            detailed_explanation=explanation,
            next_action_instructions=instructions,
            recommended_sku=None
        )
        db.add(check)
        await db.commit()
        await db.refresh(check)
        return await _build_report(check, db)

    # Step 2: Fetch device spec facts from database
    facts_stmt = (
        select(SpecFact)
        .options(selectinload(SpecFact.source))
        .where(SpecFact.device_variant_id == variant.id)
    )
    facts_res = await db.execute(facts_stmt)
    spec_facts = facts_res.scalars().all()

    # Step 3: Conflict Detection across sources (TC2)
    facts_by_field = {}
    conflicting_fields = []
    for f in spec_facts:
        if f.field_name not in facts_by_field:
            facts_by_field[f.field_name] = []
        facts_by_field[f.field_name].append(f)

    for field, facts_list in facts_by_field.items():
        norm_values = set(f.normalized_value for f in facts_list)
        if len(norm_values) > 1:
            conflicting_fields.append((field, facts_list))

    if conflicting_fields:
        # TC2: Conflicting sources detected! Return UNCERTAIN
        field_name, clashing = conflicting_fields[0]
        vals_str = ", ".join([f"{f.normalized_value} (from Source: {f.source.title})" for f in clashing])
        verdict = CompatibilityVerdict.UNCERTAIN
        summary = f"Contradictory Manufacturer Claims Detected: Multiple official records disagree on {field_name}."
        explanation = (
            f"Authoritative sources disagree on hardware specification '{field_name}': {vals_str}. "
            "Per safety guidelines, the agent will not silently pick a source or guess. "
            "Please verify the exact motherboard revision or system service tag."
        )
        instructions = "Cart actions are blocked. Further hardware revision details are required to resolve ambiguity."

        check = Check(
            id=check_id,
            request_id=request_id,
            user_input_json=req.model_dump_json(),
            resolved_device_id=device.id,
            resolved_variant_id=variant.id,
            identity_status=status_id.value,
            part_type=req.part_type.value,
            verdict=verdict.value,
            verdict_summary=summary,
            detailed_explanation=explanation,
            next_action_instructions=instructions,
            recommended_sku=None
        )
        db.add(check)

        # Add rule results for each conflicting source
        for f in clashing:
            rr = RuleResult(
                id=f"rr_{uuid.uuid4().hex[:8]}",
                check_id=check_id,
                rule_name=f"Conflict Analysis ({field_name})",
                field_name=field_name,
                required_value="Unanimous authoritative consensus",
                observed_value=f.normalized_value,
                status="UNKNOWN",
                evidence_source_id=f.source_id,
                explanation=f"Source '{f.source.title}' reports {field_name}={f.normalized_value}. Excerpt: \"{f.excerpt}\""
            )
            db.add(rr)

        await db.commit()
        await db.refresh(check)
        return await _build_report(check, db)

    # Flatten single facts
    device_facts_dict = {f.field_name: f.normalized_value for f in spec_facts}
    primary_source_id = spec_facts[0].source_id if spec_facts else None

    # Step 4: Candidate Selection & Rule Engine Evaluation
    target_sku = req.candidate_sku
    candidate_product = None

    if target_sku:
        prod_stmt = select(Product).where(Product.sku == target_sku)
        prod_res = await db.execute(prod_stmt)
        candidate_product = prod_res.scalar_one_or_none()
    else:
        # Auto-select candidate from catalog for requested part type
        prod_stmt = select(Product).where(Product.category == req.part_type.value)
        prod_res = await db.execute(prod_stmt)
        all_prods = prod_res.scalars().all()
        # Prefer RAM-A or genuine chargers
        candidate_product = next((p for p in all_prods if p.sku in ("RAM-A", "CHARGER-OEM-65W-USB-C")), all_prods[0] if all_prods else None)

    if not candidate_product:
        raise HTTPException(status_code=404, detail="No suitable candidate products found in catalog")

    candidate_specs = json.loads(candidate_product.specs_json) if candidate_product.specs_json else {}

    # Step 5: Execute Deterministic Pure Rule Engine
    if req.part_type == PartType.RAM:
        desired_cap = 16
        if req.ram_preferences and req.ram_preferences.requested_capacity_gb:
            desired_cap = req.ram_preferences.requested_capacity_gb
        verdict, comparisons, summary = evaluate_ram_compatibility(
            device_facts=device_facts_dict,
            candidate_specs=candidate_specs,
            requested_capacity_gb=desired_cap
        )
    else:
        verdict, comparisons, summary = evaluate_charger_compatibility(
            device_facts=device_facts_dict,
            candidate_specs=candidate_specs
        )

    # Detailed explanation & next action instructions
    if verdict == CompatibilityVerdict.COMPATIBLE:
        explanation = (
            f"Compatibility Verified: Candidate SKU '{candidate_product.sku}' satisfies all manufacturer "
            f"voltage, physical interface, and hardware capacity constraints for {device.brand} {device.model_family}."
        )
        instructions = "Explicit human approval is required to add this item to your cart."
        recommended_sku = candidate_product.sku
    elif verdict == CompatibilityVerdict.NOT_TRUSTED:
        explanation = (
            f"Unsubstantiated Marketing Claims: Candidate SKU '{candidate_product.sku}' claims universal compatibility "
            "without providing required voltage steps, pinout schematics, or USB PD profiles."
        )
        instructions = "Cart actions are blocked for unverified claims. Please select a certified product."
        recommended_sku = None
    elif verdict == CompatibilityVerdict.INCOMPATIBLE:
        explanation = f"Hardware Mismatch: Candidate SKU '{candidate_product.sku}' does not fit this device's hardware requirements."
        instructions = "Cart action blocked. Do not purchase this product for this laptop model."
        recommended_sku = None
    else:
        explanation = "Technical requirements could not be fully verified."
        instructions = "Cart action blocked due to uncertain evidence."
        recommended_sku = None

    check = Check(
        id=check_id,
        request_id=request_id,
        user_input_json=req.model_dump_json(),
        resolved_device_id=device.id,
        resolved_variant_id=variant.id,
        identity_status=status_id.value,
        part_type=req.part_type.value,
        verdict=verdict.value,
        verdict_summary=summary,
        detailed_explanation=explanation,
        next_action_instructions=instructions,
        recommended_sku=recommended_sku
    )
    db.add(check)

    # Persist Rule Results
    for comp in comparisons:
        rr = RuleResult(
            id=f"rr_{uuid.uuid4().hex[:8]}",
            check_id=check_id,
            rule_name=comp.rule_name,
            field_name=comp.field_name,
            required_value=comp.required_value,
            observed_value=comp.observed_value,
            status=comp.status.value,
            evidence_source_id=primary_source_id,
            explanation=comp.explanation
        )
        db.add(rr)

    # Step 6: If COMPATIBLE, generate a safe Cart Proposal (awaiting approval)
    if verdict == CompatibilityVerdict.COMPATIBLE and recommended_sku:
        proposal = CartProposal(
            id=f"prop_{uuid.uuid4().hex[:12]}",
            check_id=check_id,
            product_sku=recommended_sku,
            quantity=1,
            cart_id=req.cart_id or "default-cart",
            rationale=f"Verified compatible upgrade for {device.brand} {device.model_family}",
            version=1,
            status="AWAITING_APPROVAL",
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db.add(proposal)

    await db.commit()
    await db.refresh(check)
    return await _build_report(check, db)

@router.get("", response_model=List[CompatibilityReport])
async def list_checks(limit: int = 20, db: AsyncSession = Depends(get_db)):
    stmt = select(Check).order_by(Check.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    checks = res.scalars().all()
    reports = []
    for c in checks:
        reports.append(await _build_report(c, db))
    return reports

@router.get("/{check_id}", response_model=CompatibilityReport)
async def get_check(check_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Check).where(Check.id == check_id)
    res = await db.execute(stmt)
    check = res.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail=f"Check '{check_id}' not found")
    return await _build_report(check, db)

@router.get("/{check_id}/evidence")
async def get_check_evidence(check_id: str, db: AsyncSession = Depends(get_db)):
    report = await get_check(check_id, db)
    return {
        "check_id": check_id,
        "evidence_items": report.evidence_items
    }

@router.post("/{check_id}/clarify", response_model=CompatibilityReport)
async def clarify_check(
    check_id: str,
    req: ClarifyRequest,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Check).where(Check.id == check_id)
    res = await db.execute(stmt)
    check = res.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail=f"Check '{check_id}' not found")

    old_input = json.loads(check.user_input_json)
    # Resume the same check with updated model string
    clarified_model = req.clarified_model or old_input.get("device_model")
    new_request = CheckRequest(
        device_brand=old_input.get("device_brand"),
        device_model=clarified_model,
        part_type=PartType(old_input.get("part_type", "RAM")),
        ram_preferences=old_input.get("ram_preferences"),
        charger_preferences=old_input.get("charger_preferences"),
        candidate_sku=old_input.get("candidate_sku"),
        cart_id=old_input.get("cart_id", "default-cart")
    )

    # Re-run resolution and analysis
    return await create_check(new_request, db)
