from typing import Dict, Any, List, Tuple
from packages.shared_schemas.models import RuleStatus, CompatibilityVerdict, RuleComparison

def evaluate_charger_compatibility(
    device_facts: Dict[str, Any],
    candidate_specs: Dict[str, Any]
) -> Tuple[CompatibilityVerdict, List[RuleComparison], str]:
    """
    Evaluates Charger compatibility using deterministic pure functions.
    Hard rules:
      - Unsupported universal claim detection -> NOT_TRUSTED [S13, S23]
      - Connector geometry (USB-C vs barrel vs proprietary pinout)
      - Voltage tolerance matching (over-voltage or under-voltage can damage/fail)
      - Sufficient power (Wattage / Current capacity)
      - USB-C Power Delivery (PD) protocol negotiation verification
    """
    comparisons: List[RuleComparison] = []
    has_fail = False
    has_untrusted = False
    has_unknown = False

    # 1. Unsupported Universal Claim Check [S13, S23]
    is_universal_unverified = candidate_specs.get("unverified_claim", False) or (
        candidate_specs.get("connector") == "universal_multiple_tips" and "voltage_output" not in candidate_specs
    )
    if is_universal_unverified:
        comparisons.append(RuleComparison(
            rule_name="Seller Claims Credibility Verification",
            field_name="unverified_claim",
            required_value="Authoritative electrical & pinout documentation",
            observed_value="Generic 'universal / works with all laptops' claim without voltage/pinout matrix",
            status=RuleStatus.FAIL,
            explanation="Candidate product listing asserts 'universal compatibility' without publishing electrical voltage steps, current limits, or tip pinout schematics."
        ))
        has_untrusted = True

    # 2. Connector Geometry Check
    req_conn = str(device_facts.get("connector", "")).strip().upper()
    obs_conn = str(candidate_specs.get("connector", "")).strip().upper()

    if not req_conn:
        comparisons.append(RuleComparison(
            rule_name="Connector Geometry & Pinout",
            field_name="connector",
            required_value="Required port type",
            observed_value=obs_conn or "Missing",
            status=RuleStatus.UNKNOWN,
            explanation="Device charging port specification missing from manufacturer database."
        ))
        has_unknown = True
    elif not obs_conn:
        comparisons.append(RuleComparison(
            rule_name="Connector Geometry & Pinout",
            field_name="connector",
            required_value=req_conn,
            observed_value="Missing",
            status=RuleStatus.UNKNOWN,
            explanation="Candidate charger does not specify its output connector type."
        ))
        has_unknown = True
    elif "USB-C" in req_conn and "USB-C" not in obs_conn and "TYPE-C" not in obs_conn:
        comparisons.append(RuleComparison(
            rule_name="Connector Geometry & Pinout",
            field_name="connector",
            required_value="USB-C (Type-C)",
            observed_value=obs_conn,
            status=RuleStatus.FAIL,
            explanation=f"Physical port mismatch: Laptop accepts USB-C, but candidate charger provides {obs_conn}."
        ))
        has_fail = True
    elif "BARREL" in req_conn and "BARREL" not in obs_conn:
        comparisons.append(RuleComparison(
            rule_name="Connector Geometry & Pinout",
            field_name="connector",
            required_value=req_conn,
            observed_value=obs_conn,
            status=RuleStatus.FAIL,
            explanation=f"Physical port mismatch: Device requires {req_conn}, candidate provides {obs_conn}."
        ))
        has_fail = True
    else:
        comparisons.append(RuleComparison(
            rule_name="Connector Geometry & Pinout",
            field_name="connector",
            required_value=req_conn,
            observed_value=obs_conn,
            status=RuleStatus.PASS,
            explanation=f"Connector geometry match ({obs_conn}). Compatible with laptop chassis port."
        ))

    # 3. Voltage Matching & Tolerance
    req_volt_str = str(device_facts.get("voltage", "20.0")).replace("V", "").strip()
    try:
        req_volt = float(req_volt_str)
    except ValueError:
        req_volt = 20.0

    obs_voltages = candidate_specs.get("voltage_output")
    if not obs_voltages and "voltage" in candidate_specs:
        obs_voltages = [float(str(candidate_specs["voltage"]).replace("V", ""))]

    if not obs_voltages:
        if not is_universal_unverified:
            comparisons.append(RuleComparison(
                rule_name="Voltage Regulation & Negotiation",
                field_name="voltage",
                required_value=f"{req_volt}V DC",
                observed_value="Unspecified",
                status=RuleStatus.UNKNOWN,
                explanation="Candidate charger output voltage rating is omitted from listing."
            ))
            has_unknown = True
    else:
        # Check if required voltage is supported (within 5% for DC)
        matched_volt = any(abs(v - req_volt) <= 0.05 * req_volt for v in obs_voltages)
        if not matched_volt:
            comparisons.append(RuleComparison(
                rule_name="Voltage Regulation & Negotiation",
                field_name="voltage",
                required_value=f"{req_volt}V DC",
                observed_value=f"Supported: {obs_voltages}V",
                status=RuleStatus.FAIL,
                explanation=f"Voltage mismatch: Device requires {req_volt}V, but charger cannot deliver this voltage level. Connecting may cause hardware failure."
            ))
            has_fail = True
        else:
            comparisons.append(RuleComparison(
                rule_name="Voltage Regulation & Negotiation",
                field_name="voltage",
                required_value=f"{req_volt}V DC",
                observed_value=f"Matches required {req_volt}V profile",
                status=RuleStatus.PASS,
                explanation=f"Charger safely outputs required {req_volt}V DC power."
            ))

    # 4. Wattage / Power Capacity
    req_watts_str = str(device_facts.get("wattage", "65")).replace("W", "").strip()
    try:
        req_watts = float(req_watts_str)
    except ValueError:
        req_watts = 65.0

    obs_watts = float(candidate_specs.get("wattage", candidate_specs.get("claimed_wattage", 0)))
    if obs_watts == 0:
        if not is_universal_unverified:
            comparisons.append(RuleComparison(
                rule_name="Sufficient Power Capacity (Wattage)",
                field_name="wattage",
                required_value=f">= {req_watts}W",
                observed_value="Unspecified",
                status=RuleStatus.UNKNOWN,
                explanation="Wattage power rating not stated."
            ))
            has_unknown = True
    elif obs_watts < req_watts:
        comparisons.append(RuleComparison(
            rule_name="Sufficient Power Capacity (Wattage)",
            field_name="wattage",
            required_value=f">= {req_watts}W",
            observed_value=f"{obs_watts}W",
            status=RuleStatus.FAIL,
            explanation=f"Insufficient power: Device requires minimum {req_watts}W for charging under load, but charger only supplies {obs_watts}W."
        ))
        has_fail = True
    else:
        comparisons.append(RuleComparison(
            rule_name="Sufficient Power Capacity (Wattage)",
            field_name="wattage",
            required_value=f">= {req_watts}W",
            observed_value=f"{obs_watts}W",
            status=RuleStatus.PASS,
            explanation=f"Charger capacity ({obs_watts}W) is equal to or exceeds required device input ({req_watts}W)."
        ))

    # 5. USB-C Power Delivery (PD) protocol check [S13]
    req_protocol = device_facts.get("charging_protocol")
    if req_protocol == "USB-PD" or "USB-C" in req_conn:
        obs_pd = candidate_specs.get("pd_version") or ("PD" in str(candidate_specs.get("description", "")))
        if not obs_pd:
            comparisons.append(RuleComparison(
                rule_name="USB Power Delivery (PD) Protocol Negotiation",
                field_name="charging_protocol",
                required_value="USB PD 2.0 / 3.0 Negotiation Support",
                observed_value="Not certified / Missing PD profile specification",
                status=RuleStatus.FAIL if not is_universal_unverified else RuleStatus.UNKNOWN,
                explanation="USB-C connector shape alone does not guarantee laptop charging. Device requires active USB Power Delivery (PD) handshake to negotiate 20V."
            ))
            if not is_universal_unverified:
                has_fail = True
        else:
            comparisons.append(RuleComparison(
                rule_name="USB Power Delivery (PD) Protocol Negotiation",
                field_name="charging_protocol",
                required_value="USB PD Protocol",
                observed_value=str(candidate_specs.get("pd_version", "USB PD Compliant")),
                status=RuleStatus.PASS,
                explanation="Verified USB Power Delivery handshake capability for automated high-voltage profile negotiation."
            ))

    # 6. Overall Verdict
    if has_untrusted:
        verdict = CompatibilityVerdict.NOT_TRUSTED
        summary = "Not Trusted: Unsubstantiated seller 'universal' claim lacks verifiable pinout, voltage curves, or electrical safety certifications."
    elif has_fail:
        verdict = CompatibilityVerdict.INCOMPATIBLE
        summary = "Incompatible: Verified electrical, voltage, or connector mismatch will fail or risk damaging the device."
    elif has_unknown:
        verdict = CompatibilityVerdict.UNCERTAIN
        summary = "Uncertain: Essential electrical specifications (voltage, wattage, or connector pinout) are missing from documentation."
    else:
        verdict = CompatibilityVerdict.COMPATIBLE
        summary = f"Compatible: Charger supplies certified {obs_watts}W power with correct {obs_conn} interface and matching voltage."

    return verdict, comparisons, summary
