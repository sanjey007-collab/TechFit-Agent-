# TechFit Agent — REST API Specification

This document provides complete, production-grade documentation for the **TechFit Agent API** (`apps/api`) and the **Independent Mock Shopping Store API** (`apps/mock_store`).

---

## 1. Global Standards & Conventions

### Base URLs
- **Backend API (Local)**: `http://localhost:8000`
- **Backend API (Production/Render)**: `https://<techfit-api-host>.onrender.com`
- **Mock Store (Local)**: `http://localhost:8001`
- **Mock Store (Production/Render)**: `https://<techfit-mock-store-host>.onrender.com`

### Common Headers
| Header | Description | Required |
|---|---|---|
| `Content-Type` | `application/json` | For all `POST`, `PUT`, `PATCH` bodies |
| `Accept` | `application/json` | Recommended |
| `X-Admin-Key` | Admin secret for config/status introspection | Only for `/api/admin/*` |
| `Authorization` | `Bearer <MOCK_STORE_SERVICE_TOKEN>` | For mock store mutation endpoints |
| `Idempotency-Key` | Unique UUID/token ensuring safe mutation retry | For `/store/cart/{id}/items` and `/api/cart/proposals/{id}/approve` |

### Error Response Schema
All endpoints return standard HTTP error codes accompanied by RFC 7807-compliant JSON:
```json
{
  "detail": "Descriptive human-readable error message."
}
```

---

## 2. TechFit Backend API Reference

### 2.1 Health & Administration

#### `GET /healthz`
Health check endpoint used by Render load balancers and container orchestrators.
- **Auth**: None
- **Response `200 OK`**:
```json
{
  "status": "ok",
  "service": "techfit-api",
  "version": "1.0.0"
}
```

#### `GET /api/admin/config-status`
Returns configuration health, provider status, and smoke-test results for external keys. **Never exposes raw secrets or keys.**
- **Auth**: Header `X-Admin-Key: <ADMIN_API_KEY>`
- **Response `200 OK`**:
```json
{
  "environment": "production",
  "keys": {
    "gemini": {
      "configured": true,
      "provider": "google-genai",
      "model": "gemini-3.5-flash",
      "status": "PASS",
      "masked_key": "AQ.A****8Q"
    },
    "search": {
      "configured": true,
      "provider": "serper",
      "status": "PASS",
      "masked_key": "ffad****ed"
    },
    "product_details": {
      "configured": true,
      "provider": "serpapi",
      "status": "PASS",
      "masked_key": "2b15****0c"
    }
  },
  "mock_store": {
    "configured": true,
    "url": "https://techfit-mock-store.onrender.com"
  }
}
```
- **Error `401 Unauthorized`**: If `X-Admin-Key` is missing or invalid.

---

### 2.2 Compatibility Checks

#### `POST /api/checks`
Initiates an end-to-end agentic compatibility check. Parses natural language intent, retrieves manufacturer specifications, extracts candidate specs, runs deterministic rule evaluation, and records full audit trail.

- **Request Body**:
```json
{
  "user_query": "Will 16GB DDR4 SO-DIMM RAM work in my Lenovo ThinkPad T480?",
  "device_model": "Lenovo ThinkPad T480",
  "category": "RAM",
  "candidate_sku": "RAM-DDR4-16G-001",
  "candidate_url": null,
  "cart_id": "cart-user-123"
}
```
*Note: `device_model` and `category` are optional; if omitted, the LLM intent parser extracts them from `user_query`.*

- **Response `201 Created`**:
```json
{
  "id": "chk-a89c20ef",
  "user_query": "Will 16GB DDR4 SO-DIMM RAM work in my Lenovo ThinkPad T480?",
  "device_model": "Lenovo ThinkPad T480",
  "category": "RAM",
  "verdict": "COMPATIBLE",
  "confidence": 0.98,
  "summary": "The Crucial 16GB DDR4 2666MHz SO-DIMM is fully compatible with your Lenovo ThinkPad T480.",
  "explanation": "Your Lenovo ThinkPad T480 supports 2x DDR4 SO-DIMM slots up to 32GB total capacity. The candidate RAM matches DDR4 generation, SO-DIMM form factor, and fits within supported voltage and clock limits.",
  "specifications_found": {
    "supported_generation": "DDR4",
    "form_factor": "SO-DIMM",
    "max_capacity_gb": 32,
    "total_slots": 2,
    "soldered_ram_gb": 0,
    "max_speed_mhz": 2666
  },
  "candidate_specs": {
    "sku": "RAM-DDR4-16G-001",
    "generation": "DDR4",
    "form_factor": "SO-DIMM",
    "capacity_gb": 16,
    "speed_mhz": 2666,
    "voltage": 1.2
  },
  "comparison_table": [
    {
      "attribute": "Memory Generation",
      "required": "DDR4",
      "candidate": "DDR4",
      "match": true,
      "severity": "PASS",
      "note": "Generation match: DDR4"
    },
    {
      "attribute": "Form Factor",
      "required": "SO-DIMM",
      "candidate": "SO-DIMM",
      "match": true,
      "severity": "PASS",
      "note": "Form factor match: SO-DIMM"
    },
    {
      "attribute": "Capacity & Slots",
      "required": "Max 32GB across 2 slots",
      "candidate": "16GB",
      "match": true,
      "severity": "PASS",
      "note": "Available slot capacity permits 16GB module"
    }
  ],
  "sources": [
    {
      "title": "ThinkPad T480 Platform Specifications - Lenovo PSREF",
      "url": "https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_T480/ThinkPad_T480_Spec.PDF",
      "is_official": true,
      "reliability": "HIGH",
      "excerpt": "Memory: Up to 32GB DDR4-2400 / 2666, two 260-pin SO-DIMM sockets"
    }
  ],
  "agent_timeline": [
    {"stage": "INTENT_PARSING", "status": "COMPLETED", "message": "Parsed device: Lenovo ThinkPad T480, Category: RAM"},
    {"stage": "RETRIEVAL", "status": "COMPLETED", "message": "Retrieved official PSREF spec sheet"},
    {"stage": "EXTRACTION", "status": "COMPLETED", "message": "Extracted device limits: 32GB max, DDR4 SO-DIMM"},
    {"stage": "RULE_EVALUATION", "status": "COMPLETED", "message": "Deterministic rule engine evaluated 5 rules: All PASS"},
    {"stage": "EXPLANATION", "status": "COMPLETED", "message": "Generated clear technical rationale"}
  ],
  "cart_proposal": {
    "proposal_id": "prp-e12b774a",
    "sku": "RAM-DDR4-16G-001",
    "title": "Crucial 16GB DDR4 2666MHz SO-DIMM Memory Module",
    "price": 38.99,
    "status": "PENDING_APPROVAL"
  },
  "created_at": "2026-10-25T08:30:00Z"
}
```

- **Ambiguous Query (`MORE_INFO_REQUIRED`) Response Example**:
```json
{
  "id": "chk-b921d3fa",
  "user_query": "I need RAM for my Dell laptop",
  "device_model": "Dell Laptop",
  "category": "RAM",
  "verdict": "MORE_INFO_REQUIRED",
  "summary": "Ambiguous model detected. 'Dell Laptop' represents a brand, not a specific model.",
  "clarification_prompt": "Could you provide your exact Dell model or Service Tag? (e.g., 'Dell XPS 13 9310' or 'Dell Latitude 5420')",
  "agent_timeline": [
    {"stage": "INTENT_PARSING", "status": "NEEDS_CLARIFICATION", "message": "Device model family is too broad to locate specific technical tolerances."}
  ]
}
```

#### `GET /api/checks`
Lists historical compatibility checks with optional filters and pagination.
- **Query Parameters**:
  - `limit` (int, default `20`)
  - `category` (string, optional: `RAM` or `CHARGER`)
  - `verdict` (string, optional: `COMPATIBLE`, `INCOMPATIBLE`, `UNCERTAIN`, `MORE_INFO_REQUIRED`, `NOT_TRUSTED`)
- **Response `200 OK`**: Array of check summaries.

#### `GET /api/checks/{id}`
Retrieves full details of a compatibility check by ID.
- **Response `200 OK`**: Same as `POST /api/checks` response.
- **Error `404 Not Found`**: If check ID does not exist.

#### `POST /api/checks/{id}/clarify`
Resumes an ambiguous check (`MORE_INFO_REQUIRED`) with the user's specific response.
- **Request Body**:
```json
{
  "user_response": "Dell XPS 15 9570"
}
```
- **Response `200 OK`**: Returns updated check object with resumed analysis, fetched specs, and deterministic verdict.

---

### 2.3 Catalog & Store Integration

#### `GET /api/products`
Lists available catalog products from the mock store and fixture inventory.
- **Query Parameters**:
  - `category` (string, optional: `RAM`, `CHARGER`)
  - `search` (string, optional)
- **Response `200 OK`**:
```json
[
  {
    "sku": "RAM-DDR4-16G-001",
    "title": "Crucial 16GB DDR4 2666MHz SO-DIMM Memory Module",
    "category": "RAM",
    "price": 38.99,
    "specs": {
      "generation": "DDR4",
      "form_factor": "SO-DIMM",
      "capacity_gb": 16,
      "speed_mhz": 2666,
      "voltage": 1.2
    },
    "in_stock": true
  }
]
```

---

### 2.4 Human Approval & Cart Orchestration

#### `POST /api/cart/proposals`
Creates a cart addition proposal for a verified compatible product.
- **Security Guard**: Will return `400 Bad Request` if the associated check verdict is not `COMPATIBLE`.
- **Request Body**:
```json
{
  "check_id": "chk-a89c20ef",
  "sku": "RAM-DDR4-16G-001",
  "quantity": 1,
  "cart_id": "cart-user-123"
}
```

#### `POST /api/cart/proposals/{id}/approve`
**Human Approval Gate**: Commits the proposed SKU to the independent mock store cart. Ensures strict idempotency and SKU immutability.
- **Headers**:
  - `Idempotency-Key`: Optional client UUID to guard against network retries.
- **Request Body**:
```json
{
  "proposal_id": "prp-e12b774a",
  "confirmed": true,
  "user_name": "Sanjey"
}
```
- **Response `200 OK`**:
```json
{
  "status": "APPROVED",
  "proposal_id": "prp-e12b774a",
  "cart_id": "cart-user-123",
  "sku": "RAM-DDR4-16G-001",
  "quantity": 1,
  "approved_at": "2026-10-25T08:35:12Z",
  "store_response": {
    "success": true,
    "cart_item_id": "item-99120",
    "sku": "RAM-DDR4-16G-001",
    "quantity": 1
  },
  "verification": {
    "verified": true,
    "matched_sku": "RAM-DDR4-16G-001",
    "expected_sku": "RAM-DDR4-16G-001",
    "cart_total": 38.99,
    "message": "Independent verifier confirmed SKU RAM-DDR4-16G-001 exists in mock store cart."
  }
}
```
- **Error `400 Bad Request`**: If `confirmed` is `false` or proposal was previously rejected.
- **Error `409 Conflict`**: If the proposal was already executed with different parameters.

#### `GET /api/cart/{cart_id}`
**Independent Verifier Endpoint**: Reads the live cart state directly from the mock store and independently verifies whether the expected compatible items exist without trusting agent memory.
- **Response `200 OK`**:
```json
{
  "cart_id": "cart-user-123",
  "items": [
    {
      "sku": "RAM-DDR4-16G-001",
      "title": "Crucial 16GB DDR4 2666MHz SO-DIMM Memory Module",
      "price": 38.99,
      "quantity": 1
    }
  ],
  "total_items": 1,
  "subtotal": 38.99,
  "verification_audit": {
    "verified": true,
    "verified_at": "2026-10-25T08:35:15Z",
    "verifier": "IndependentStoreVerifier"
  }
}
```

---

### 2.5 Test Dashboard Runner API

#### `POST /api/tests/run`
Executes the live automated test suite on demand. Runs all official test cases (TC1–TC4), negative/security suites, and live provider smoke tests.
- **Response `200 OK`**:
```json
{
  "run_id": "run-20261025-0830",
  "timestamp": "2026-10-25T08:30:15Z",
  "total_tests": 28,
  "passed": 28,
  "failed": 0,
  "duration_seconds": 8.55,
  "test_cases": [
    {
      "id": "TC1",
      "name": "DDR4 Laptop Compatibility Check",
      "device": "Lenovo ThinkPad T480",
      "expected_verdict": "COMPATIBLE",
      "actual_verdict": "COMPATIBLE",
      "status": "PASS",
      "latency_ms": 340
    },
    {
      "id": "TC2",
      "name": "Conflicting Specifications Handling",
      "device": "Dell Inspiron 15 5570",
      "expected_verdict": "UNCERTAIN",
      "actual_verdict": "UNCERTAIN",
      "status": "PASS",
      "latency_ms": 280
    },
    {
      "id": "TC3",
      "name": "Ambiguous Model Clarification",
      "device": "Dell Laptop",
      "expected_verdict": "MORE_INFO_REQUIRED",
      "actual_verdict": "MORE_INFO_REQUIRED",
      "status": "PASS",
      "latency_ms": 190
    },
    {
      "id": "TC4",
      "name": "Untrusted Universal Charger Claim",
      "device": "Asus ROG Zephyrus G14",
      "expected_verdict": "NOT_TRUSTED",
      "actual_verdict": "NOT_TRUSTED",
      "status": "PASS",
      "latency_ms": 210
    }
  ]
}
```

---

## 3. Independent Mock Store API Reference (`apps/mock_store`)

The mock shopping store operates as an isolated service running on port 8001 (or separate Render service).

### `GET /healthz`
Returns service availability status.
```json
{"status": "ok", "service": "techfit-mock-store"}
```

### `GET /store/products`
Lists all products in the mock store database.
- **Response**: Array of store product items with SKU, price, stock, specs.

### `GET /store/cart/{id}`
Returns the current items and state of a cart.
- **Response**:
```json
{
  "cart_id": "cart-user-123",
  "items": [
    {
      "sku": "RAM-DDR4-16G-001",
      "title": "Crucial 16GB DDR4 2666MHz SO-DIMM Memory Module",
      "price": 38.99,
      "quantity": 1
    }
  ],
  "subtotal": 38.99
}
```

### `POST /store/cart/{id}/items`
Adds an item to a cart. Requires service authentication and supports idempotency.
- **Headers**:
  - `Authorization: Bearer <MOCK_STORE_SERVICE_TOKEN>`
  - `Idempotency-Key: <unique-token>` (Optional but recommended)
- **Request Body**:
```json
{
  "sku": "RAM-DDR4-16G-001",
  "quantity": 1
}
```
- **Response `201 Created`**:
```json
{
  "success": true,
  "cart_id": "cart-user-123",
  "sku": "RAM-DDR4-16G-001",
  "quantity": 1
}
```
- **Error `401 Unauthorized`**: If Bearer token is missing or incorrect.
- **Error `404 Not Found`**: If SKU is not found in store catalog.
