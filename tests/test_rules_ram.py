import pytest
from apps.api.services.rule_engine.ram_rules import evaluate_ram_compatibility
from packages.shared_schemas.models import CompatibilityVerdict, RuleStatus

def test_ram_rule_exact_match():
    device_facts = {
        "ddr_generation": "DDR4",
        "form_factor": "SO-DIMM",
        "available_slots": "1",
        "max_capacity_gb": "32",
        "installed_ram_gb": "8"
    }
    candidate_specs = {
        "ddr_generation": "DDR4",
        "form_factor": "SO-DIMM",
        "capacity_gb": 16,
        "speed_mhz": 3200
    }
    verdict, comparisons, summary = evaluate_ram_compatibility(device_facts, candidate_specs, 16)
    assert verdict == CompatibilityVerdict.COMPATIBLE
    assert all(c.status == RuleStatus.PASS for c in comparisons)

def test_ram_rule_ddr_mismatch():
    device_facts = {
        "ddr_generation": "DDR4",
        "form_factor": "SO-DIMM",
        "available_slots": "1",
        "max_capacity_gb": "32"
    }
    candidate_specs = {
        "ddr_generation": "DDR5",
        "form_factor": "SO-DIMM",
        "capacity_gb": 16
    }
    verdict, comparisons, summary = evaluate_ram_compatibility(device_facts, candidate_specs, 16)
    assert verdict == CompatibilityVerdict.INCOMPATIBLE
    ddr_comp = next(c for c in comparisons if c.field_name == "ddr_generation")
    assert ddr_comp.status == RuleStatus.FAIL

def test_ram_rule_form_factor_mismatch():
    device_facts = {
        "ddr_generation": "DDR4",
        "form_factor": "SO-DIMM",
        "available_slots": "1"
    }
    candidate_specs = {
        "ddr_generation": "DDR4",
        "form_factor": "DIMM", # Desktop DIMM
        "capacity_gb": 16
    }
    verdict, comparisons, summary = evaluate_ram_compatibility(device_facts, candidate_specs, 16)
    assert verdict == CompatibilityVerdict.INCOMPATIBLE
    form_comp = next(c for c in comparisons if c.field_name == "form_factor")
    assert form_comp.status == RuleStatus.FAIL

def test_ram_rule_soldered_zero_slots():
    device_facts = {
        "ddr_generation": "DDR4",
        "form_factor": "SO-DIMM",
        "available_slots": "0" # Fully soldered or 0 slots available
    }
    candidate_specs = {
        "ddr_generation": "DDR4",
        "form_factor": "SO-DIMM",
        "capacity_gb": 16
    }
    verdict, comparisons, summary = evaluate_ram_compatibility(device_facts, candidate_specs, 16)
    assert verdict == CompatibilityVerdict.INCOMPATIBLE
    slot_comp = next(c for c in comparisons if c.field_name == "available_slots")
    assert slot_comp.status == RuleStatus.FAIL

def test_ram_rule_capacity_exceeded():
    device_facts = {
        "ddr_generation": "DDR4",
        "form_factor": "SO-DIMM",
        "available_slots": "1",
        "max_capacity_gb": "16",
        "installed_ram_gb": "8"
    }
    # 8GB installed + 16GB upgrade = 24GB > 16GB max!
    candidate_specs = {
        "ddr_generation": "DDR4",
        "form_factor": "SO-DIMM",
        "capacity_gb": 16
    }
    verdict, comparisons, summary = evaluate_ram_compatibility(device_facts, candidate_specs, 16)
    assert verdict == CompatibilityVerdict.INCOMPATIBLE
    cap_comp = next(c for c in comparisons if c.field_name == "max_capacity_gb")
    assert cap_comp.status == RuleStatus.FAIL
