import pytest
from apps.api.services.rule_engine.charger_rules import evaluate_charger_compatibility
from packages.shared_schemas.models import CompatibilityVerdict, RuleStatus

def test_charger_unsupported_universal_claim():
    device_facts = {
        "connector": "USB-C",
        "wattage": "65",
        "voltage": "20.0"
    }
    candidate_specs = {
        "connector": "universal_multiple_tips",
        "claimed_wattage": 90,
        "unverified_claim": True
    }
    verdict, comparisons, summary = evaluate_charger_compatibility(device_facts, candidate_specs)
    assert verdict == CompatibilityVerdict.NOT_TRUSTED
    claim_comp = next(c for c in comparisons if c.field_name == "unverified_claim")
    assert claim_comp.status == RuleStatus.FAIL

def test_charger_exact_match_usb_c_pd():
    device_facts = {
        "connector": "USB-C",
        "wattage": "65",
        "voltage": "20.0",
        "charging_protocol": "USB-PD"
    }
    candidate_specs = {
        "connector": "USB-C",
        "wattage": 65,
        "voltage_output": [20.0, 15.0, 9.0, 5.0],
        "pd_version": "PD 3.0"
    }
    verdict, comparisons, summary = evaluate_charger_compatibility(device_facts, candidate_specs)
    assert verdict == CompatibilityVerdict.COMPATIBLE
    assert all(c.status == RuleStatus.PASS for c in comparisons)

def test_charger_voltage_mismatch():
    device_facts = {
        "connector": "Barrel 4.5mm",
        "wattage": "45",
        "voltage": "19.5"
    }
    candidate_specs = {
        "connector": "Barrel 4.5mm",
        "wattage": 45,
        "voltage_output": [12.0] # Severe under-voltage
    }
    verdict, comparisons, summary = evaluate_charger_compatibility(device_facts, candidate_specs)
    assert verdict == CompatibilityVerdict.INCOMPATIBLE
    volt_comp = next(c for c in comparisons if c.field_name == "voltage")
    assert volt_comp.status == RuleStatus.FAIL

def test_charger_insufficient_wattage():
    device_facts = {
        "connector": "USB-C",
        "wattage": "65",
        "voltage": "20.0"
    }
    candidate_specs = {
        "connector": "USB-C",
        "wattage": 30, # Only 30W phone charger
        "voltage_output": [20.0, 15.0, 9.0],
        "pd_version": "PD 3.0"
    }
    verdict, comparisons, summary = evaluate_charger_compatibility(device_facts, candidate_specs)
    assert verdict == CompatibilityVerdict.INCOMPATIBLE
    watt_comp = next(c for c in comparisons if c.field_name == "wattage")
    assert watt_comp.status == RuleStatus.FAIL
