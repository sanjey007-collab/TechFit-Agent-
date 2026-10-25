import type {
  CompatibilityReport,
  CartState,
  TestRunSummary,
  ConfigStatusResponse
} from "./types";

let rawApi = import.meta.env.VITE_API_URL || "http://localhost:8000";
if (rawApi && !rawApi.startsWith("http://") && !rawApi.startsWith("https://")) {
  rawApi = `https://${rawApi}`;
}
const API_BASE = rawApi.replace(/\/+$/, "");

export async function checkHealth(): Promise<{ status: string; service: string }> {
  const resp = await fetch(`${API_BASE}/healthz`);
  if (!resp.ok) throw new Error(`Health check failed: ${resp.status}`);
  return resp.json();
}

export async function fetchConfigStatus(): Promise<ConfigStatusResponse> {
  const resp = await fetch(`${API_BASE}/api/admin/config-status`);
  if (!resp.ok) throw new Error(`Config status failed: ${resp.status}`);
  return resp.json();
}

export async function runCompatibilityCheck(payload: {
  device_brand?: string;
  device_model: string;
  part_type: string;
  ram_preferences?: { requested_capacity_gb?: number };
  charger_preferences?: { candidate_sku?: string };
  candidate_sku?: string;
  natural_language_query?: string;
  cart_id?: string;
}): Promise<CompatibilityReport> {
  const resp = await fetch(`${API_BASE}/api/checks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Compatibility check request failed");
  }
  return resp.json();
}

export async function clarifyCheck(checkId: string, payload: {
  clarified_model?: string;
  clarified_variant?: string;
}): Promise<CompatibilityReport> {
  const resp = await fetch(`${API_BASE}/api/checks/${checkId}/clarify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Clarification failed" }));
    throw new Error(err.detail || "Failed to submit clarification");
  }
  return resp.json();
}

export async function approveProposal(proposalId: string, payload: {
  proposal_id?: string;
  check_id: string;
  product_sku: string;
  proposal_version: number;
  idempotency_key: string;
}): Promise<{ action_id: string; status: string; message: string }> {
  const body = { proposal_id: proposalId, ...payload };
  const resp = await fetch(`${API_BASE}/api/cart/proposals/${proposalId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Approval failed" }));
    throw new Error(err.detail || "Approval request failed");
  }
  return resp.json();
}

export async function fetchCart(cartId: string = "default-cart"): Promise<CartState> {
  const resp = await fetch(`${API_BASE}/api/cart/${cartId}`);
  if (!resp.ok) throw new Error(`Failed to load cart: ${resp.status}`);
  return resp.json();
}

export async function runOfficialTests(): Promise<TestRunSummary> {
  const resp = await fetch(`${API_BASE}/api/tests/run`, {
    method: "POST"
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Test execution failed" }));
    throw new Error(err.detail || "Test execution request failed");
  }
  return resp.json();
}

export async function fetchRecentChecks(): Promise<CompatibilityReport[]> {
  const resp = await fetch(`${API_BASE}/api/checks`);
  if (!resp.ok) return [];
  return resp.json();
}
