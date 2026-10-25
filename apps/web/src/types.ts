export type PartType = "RAM" | "CHARGER";

export type DeviceIdentityStatus = "RESOLVED" | "AMBIGUOUS" | "NOT_FOUND" | "INSUFFICIENT_INPUT";

export type CompatibilityVerdict = "COMPATIBLE" | "INCOMPATIBLE" | "UNCERTAIN" | "MORE_INFO_REQUIRED" | "NOT_TRUSTED";

export type RuleStatus = "PASS" | "FAIL" | "UNKNOWN";

export type ProposalStatus = "PROPOSED" | "AWAITING_APPROVAL" | "EXECUTED" | "EXPIRED" | "REJECTED";

export type VerificationStatus = "VERIFIED" | "FAILED" | "PENDING";

export interface RuleComparison {
  rule_name: string;
  field_name: string;
  required_value: string;
  observed_value: string;
  status: RuleStatus;
  evidence_source_id?: string;
  explanation: string;
}

export interface EvidenceItem {
  source_id: string;
  url: string;
  title: string;
  domain: string;
  excerpt: string;
  retrieval_timestamp: string;
  applicability: string;
  is_official: boolean;
}

export interface CartProposalResponse {
  proposal_id: string;
  check_id: string;
  product_sku: string;
  product_name: string;
  quantity: number;
  price: number;
  cart_id: string;
  rationale: string;
  version: number;
  status: ProposalStatus;
  expires_at: string;
  created_at: string;
}

export interface CartVerificationResponse {
  verification_id: string;
  action_id: string;
  cart_id: string;
  expected_sku: string;
  expected_qty: number;
  observed_sku?: string;
  observed_qty: number;
  status: VerificationStatus;
  verified_at: string;
  details: string;
}

export interface CompatibilityReport {
  check_id: string;
  request_id: string;
  identity_status: DeviceIdentityStatus;
  resolved_device_brand?: string;
  resolved_device_model?: string;
  resolved_variant?: string;
  part_type: PartType;
  verdict: CompatibilityVerdict;
  verdict_summary: string;
  detailed_explanation: string;
  comparisons: RuleComparison[];
  evidence_items: EvidenceItem[];
  recommended_sku?: string;
  proposal?: CartProposalResponse;
  verification?: CartVerificationResponse;
  next_action_instructions: string;
  created_at: string;
  updated_at: string;
}

export interface CartItem {
  sku: string;
  title: string;
  brand: string;
  category: string;
  quantity: number;
  price_per_unit: number;
  total_price: number;
}

export interface CartState {
  cart_id: string;
  item_count: number;
  subtotal: number;
  items: CartItem[];
}

export interface TestRunItem {
  test_case_id: string;
  test_name: string;
  input_summary: string;
  expected_verdict: string;
  actual_verdict: string;
  expected_cart_status: string;
  actual_cart_status: string;
  pass_fail: "PASS" | "FAIL";
  logs: string[];
  duration_ms: number;
}

export interface TestRunSummary {
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  overall_status: string;
  executed_at: string;
  test_results: TestRunItem[];
}

export interface ConfigStatusResponse {
  status: string;
  authenticated: boolean;
  keys: {
    gemini: { configured: boolean; masked?: string; model: string; provider: string };
    search: { configured: boolean; masked?: string; provider: string };
    product_details: { configured: boolean; masked?: string; provider: string };
  };
  services: {
    database: { engine: string; connected: boolean };
    mock_store: { url: string; token_configured: boolean };
  };
}
