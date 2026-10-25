from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class PartType(str, Enum):
    RAM = "RAM"
    CHARGER = "CHARGER"

class DeviceIdentityStatus(str, Enum):
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_FOUND = "NOT_FOUND"
    INSUFFICIENT_INPUT = "INSUFFICIENT_INPUT"

class CompatibilityVerdict(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNCERTAIN = "UNCERTAIN"
    MORE_INFO_REQUIRED = "MORE_INFO_REQUIRED"
    NOT_TRUSTED = "NOT_TRUSTED"

class RuleStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"

class ProposalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"

class ActionStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    PENDING = "PENDING"

# --- Request / Response Models ---

class RamPreferences(BaseModel):
    requested_capacity_gb: Optional[int] = Field(None, description="Desired capacity in GB, e.g. 16")
    requested_speed_mhz: Optional[int] = Field(None, description="Optional desired speed, e.g. 3200")
    budget_max: Optional[float] = Field(None, description="Max budget")

class ChargerPreferences(BaseModel):
    replacement_need: Optional[str] = Field(None, description="e.g. Travel, replacement, high power")
    candidate_sku: Optional[str] = Field(None, description="Optional target SKU to test")

class CheckRequest(BaseModel):
    device_brand: Optional[str] = Field(None, description="Brand name, e.g. Lenovo, Dell, HP")
    device_model: str = Field(..., description="Exact model number or identifier")
    part_type: PartType = Field(..., description="RAM or CHARGER")
    ram_preferences: Optional[RamPreferences] = None
    charger_preferences: Optional[ChargerPreferences] = None
    candidate_sku: Optional[str] = Field(None, description="Candidate product SKU to evaluate")
    natural_language_query: Optional[str] = Field(None, description="Free text user query")
    cart_id: Optional[str] = Field("default-cart", description="Target shopping cart ID")

class ClarifyRequest(BaseModel):
    clarified_model: Optional[str] = Field(None, description="Precise model or service tag supplied by user")
    clarified_variant: Optional[str] = Field(None, description="Specific sub-variant, e.g. 20L5CTO1WW")
    additional_notes: Optional[str] = None

class RuleComparison(BaseModel):
    rule_name: str
    field_name: str
    required_value: str
    observed_value: str
    status: RuleStatus
    evidence_source_id: Optional[str] = None
    explanation: str

class EvidenceItem(BaseModel):
    source_id: str
    url: str
    title: str
    domain: str
    excerpt: str
    retrieval_timestamp: str
    applicability: str
    is_official: bool

class CartProposalResponse(BaseModel):
    proposal_id: str
    check_id: str
    product_sku: str
    product_name: str
    quantity: int
    price: float
    cart_id: str
    rationale: str
    version: int
    status: ProposalStatus
    expires_at: str
    created_at: str

class CartProposalCreate(BaseModel):
    check_id: str
    product_sku: str
    quantity: int = 1
    cart_id: str = "default-cart"
    rationale: str

class CartApprovalRequest(BaseModel):
    proposal_id: str
    check_id: str
    product_sku: str
    proposal_version: int
    idempotency_key: str

class CartApprovalResponse(BaseModel):
    action_id: str
    proposal_id: str
    status: ActionStatus
    executed_at: str
    message: str

class CartVerificationResponse(BaseModel):
    verification_id: str
    action_id: str
    cart_id: str
    expected_sku: str
    expected_qty: int
    observed_sku: Optional[str]
    observed_qty: int
    status: VerificationStatus
    verified_at: str
    details: str

class CompatibilityReport(BaseModel):
    check_id: str
    request_id: str
    identity_status: DeviceIdentityStatus
    resolved_device_brand: Optional[str] = None
    resolved_device_model: Optional[str] = None
    resolved_variant: Optional[str] = None
    part_type: PartType
    verdict: CompatibilityVerdict
    verdict_summary: str
    detailed_explanation: str
    comparisons: List[RuleComparison] = []
    evidence_items: List[EvidenceItem] = []
    recommended_sku: Optional[str] = None
    proposal: Optional[CartProposalResponse] = None
    verification: Optional[CartVerificationResponse] = None
    next_action_instructions: str
    created_at: str
    updated_at: str

class TestRunItem(BaseModel):
    test_case_id: str
    test_name: str
    input_summary: str
    expected_verdict: str
    actual_verdict: str
    expected_cart_status: str
    actual_cart_status: str
    pass_fail: str
    logs: List[str] = []
    duration_ms: float

class TestRunSummary(BaseModel):
    total_tests: int
    passed_tests: int
    failed_tests: int
    overall_status: str
    executed_at: str
    test_results: List[TestRunItem]

class KeyConfigStatus(BaseModel):
    configured: bool
    masked_key: Optional[str] = None
    last_smoke_test: str
    provider: str

class ConfigStatusResponse(BaseModel):
    gemini: KeyConfigStatus
    search: KeyConfigStatus
    product_details: KeyConfigStatus
    database: Dict[str, Any]
    mock_store: Dict[str, Any]
