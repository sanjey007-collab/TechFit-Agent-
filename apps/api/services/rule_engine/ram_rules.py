from typing import Dict, Any, List, Tuple
from packages.shared_schemas.models import RuleStatus, CompatibilityVerdict, RuleComparison

def evaluate_ram_compatibility(
    device_facts: Dict[str, Any],
    candidate_specs: Dict[str, Any],
    requested_capacity_gb: int = 16
) -> Tuple[CompatibilityVerdict, List[RuleComparison], str]:
    """
    Evaluates RAM compatibility using deterministic pure functions.
    Hard rules:
      - DDR generation match (DDR4 vs DDR5)
      - Physical Form Factor match (SO-DIMM for laptops vs full-size DIMM)
      - Upgrade path: available slots
      - Total memory capacity ceiling
    """
    comparisons: List[RuleComparison] = []
    has_fail = False
    has_unknown = False

    # 1. DDR Generation
    req_ddr = device_facts.get("ddr_generation", "").upper()
    obs_ddr = candidate_specs.get("ddr_generation", "").upper()

    if not req_ddr:
        comparisons.append(RuleComparison(
            rule_name="DDR Generation Validation",
            field_name="ddr_generation",
            required_value="Required DDR Generation",
            observed_value=obs_ddr or "Missing",
            status=RuleStatus.UNKNOWN,
            explanation="Device motherboard memory standard is missing from manufacturer records."
        ))
        has_unknown = True
    elif not obs_ddr:
        comparisons.append(RuleComparison(
            rule_name="DDR Generation Validation",
            field_name="ddr_generation",
            required_value=req_ddr,
            observed_value="Missing",
            status=RuleStatus.UNKNOWN,
            explanation="Candidate RAM module does not declare its DDR generation standard."
        ))
        has_unknown = True
    elif req_ddr != obs_ddr:
        comparisons.append(RuleComparison(
            rule_name="DDR Generation Validation",
            field_name="ddr_generation",
            required_value=req_ddr,
            observed_value=obs_ddr,
            status=RuleStatus.FAIL,
            explanation=f"Critical hardware mismatch: Motherboard requires {req_ddr}, but candidate product is {obs_ddr}. Not pin-compatible."
        ))
        has_fail = True
    else:
        comparisons.append(RuleComparison(
            rule_name="DDR Generation Validation",
            field_name="ddr_generation",
            required_value=req_ddr,
            observed_value=obs_ddr,
            status=RuleStatus.PASS,
            explanation=f"Exact match on memory generation ({req_ddr})."
        ))

    # 2. Form Factor (SO-DIMM vs DIMM)
    req_form = device_facts.get("form_factor", "SO-DIMM").upper()
    obs_form = candidate_specs.get("form_factor", "").upper()

    if not obs_form:
        comparisons.append(RuleComparison(
            rule_name="Physical Form Factor Check",
            field_name="form_factor",
            required_value=req_form,
            observed_value="Missing",
            status=RuleStatus.UNKNOWN,
            explanation="Candidate module form factor (SO-DIMM vs DIMM) is not specified in listing."
        ))
        has_unknown = True
    elif "SO-DIMM" in req_form and "SO-DIMM" not in obs_form:
        comparisons.append(RuleComparison(
            rule_name="Physical Form Factor Check",
            field_name="form_factor",
            required_value="SO-DIMM (Laptop 260/262-pin)",
            observed_value=obs_form,
            status=RuleStatus.FAIL,
            explanation=f"Form factor mismatch: Laptop requires compact SO-DIMM, but candidate is {obs_form} (Desktop size, physically will not fit)."
        ))
        has_fail = True
    else:
        comparisons.append(RuleComparison(
            rule_name="Physical Form Factor Check",
            field_name="form_factor",
            required_value=req_form,
            observed_value=obs_form,
            status=RuleStatus.PASS,
            explanation=f"Physical form factor matched ({obs_form}). Fits standard notebook memory sockets."
        ))

    # 3. Available Slots & Upgrade Path
    avail_slots_str = str(device_facts.get("available_slots", "1"))
    try:
        avail_slots = int(avail_slots_str)
    except ValueError:
        avail_slots = 1

    if avail_slots <= 0:
        comparisons.append(RuleComparison(
            rule_name="Physical Slot Availability",
            field_name="available_slots",
            required_value=">= 1 available slot",
            observed_value=f"{avail_slots} available slots",
            status=RuleStatus.FAIL,
            explanation="Motherboard memory slots are fully populated or memory is entirely soldered (non-upgradable)."
        ))
        has_fail = True
    else:
        comparisons.append(RuleComparison(
            rule_name="Physical Slot Availability",
            field_name="available_slots",
            required_value=">= 1 available slot",
            observed_value=f"{avail_slots} available slot(s)",
            status=RuleStatus.PASS,
            explanation=f"Device has {avail_slots} open expansion slot available for memory addition."
        ))

    # 4. Total Capacity Ceiling
    max_cap_str = str(device_facts.get("max_capacity_gb", "32"))
    try:
        max_cap = int(max_cap_str)
    except ValueError:
        max_cap = 32

    installed_cap_str = str(device_facts.get("installed_ram_gb", "8"))
    try:
        installed_cap = int(installed_cap_str)
    except ValueError:
        installed_cap = 8

    cand_cap = candidate_specs.get("capacity_gb", requested_capacity_gb)
    projected_total = installed_cap + cand_cap

    if projected_total > max_cap:
        comparisons.append(RuleComparison(
            rule_name="Maximum Memory Capacity",
            field_name="max_capacity_gb",
            required_value=f"<= {max_cap}GB total",
            observed_value=f"{projected_total}GB ({installed_cap}GB installed + {cand_cap}GB candidate)",
            status=RuleStatus.FAIL,
            explanation=f"Capacity exceeded: Adding {cand_cap}GB to existing {installed_cap}GB results in {projected_total}GB, exceeding chipset ceiling of {max_cap}GB."
        ))
        has_fail = True
    else:
        comparisons.append(RuleComparison(
            rule_name="Maximum Memory Capacity",
            field_name="max_capacity_gb",
            required_value=f"<= {max_cap}GB total",
            observed_value=f"{projected_total}GB ({installed_cap}GB + {cand_cap}GB)",
            status=RuleStatus.PASS,
            explanation=f"Upgrade within chipset limits ({projected_total}GB projected <= {max_cap}GB maximum)."
        ))

    # 5. Determine Verdict
    if has_fail:
        verdict = CompatibilityVerdict.INCOMPATIBLE
        summary = "Incompatible: One or more verified physical or architectural constraints failed."
    elif has_unknown:
        verdict = CompatibilityVerdict.UNCERTAIN
        summary = "Uncertain: Critical motherboard or module specifications could not be verified from authoritative documentation."
    else:
        verdict = CompatibilityVerdict.COMPATIBLE
        summary = f"Compatible: Verified {req_ddr} {obs_form} {cand_cap}GB module satisfies all manufacturer chipset, physical socket, and capacity requirements."

    return verdict, comparisons, summary
