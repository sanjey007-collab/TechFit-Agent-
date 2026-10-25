# TechFit Agent — Hackathon Judge Demo Walkthrough Script

**Project Title:** AI Product Compatibility Checker Agent (TechFit Agent)  
**Track:** Commerce & Consumer AI — Agentic Hardware Compatibility Engine  
**Presentation Reference:** `Product_Compatibility_Checker_Black_White.pptx` [S1–S29]

---

## 1. Executive Summary & Problem Framing (1 Minute)
- **The Problem [S3]:** Buying replacement laptop RAM or power chargers is notoriously error-prone. RAM differs by DDR generation, form factor (SO-DIMM vs desktop DIMM), and soldered motherboard layouts. Chargers differ by barrel vs USB-C, voltage curves, wattage, and USB Power Delivery (PD) negotiation. Misleading product claims like "universal fit" cause wasted money and electrical hazards.
- **The Agentic AI Solution [S5, S8]:** TechFit is **not a chatbot**. It is an autonomous agent with:
  1. Real-time manufacturer specification retrieval via Search APIs.
  2. Grounded fact extraction with verbatim excerpt verification (provenance).
  3. **Deterministic rule engines** (pure mathematical functions) for hardware comparison — the LLM is physically barred from computing verdicts or modifying carts.
  4. Mandatory **Human-in-the-Loop Approval** with idempotency keys.
  5. An **Independent Cart Verifier** reading actual store state directly from an isolated Mock Store API.

---

## 2. Live Demo Script & Mandatory Test Cases (4 Minutes)

### Step 1: Open the Live Application
- Navigate to the deployed frontend on Render: `https://techfit-web.onrender.com` (or local run `http://localhost:5173`).
- Point out the **Live Agent Execution Pipeline** (Identify → Retrieve → Validate → Compare → Explain → Approve → Verify).

---

### Step 2: Official TC1 — Compatible DDR4 Laptop Upgrade [S20]
1. Click **"TC1: DDR4 Laptop"** in the quick fixtures.
   - Input: Model `DEMO-LAPTOP-001`, Part `RAM`, Upgrade `16 GB`.
2. Click **"Verify Technical Compatibility"**.
3. **Show the Judge:**
   - **Verdict Banner:** `COMPATIBLE` (Emerald).
   - **Rule Comparisons Table:**
     - `DDR Generation Validation`: Required DDR4 vs Observed DDR4 → `PASS`
     - `Physical Form Factor Check`: Required SO-DIMM vs Observed SO-DIMM → `PASS`
     - `Physical Slot Availability`: 1 open slot available → `PASS`
     - `Maximum Memory Capacity`: Projected 24GB <= 32GB chipset ceiling → `PASS`
   - **Evidence Drawer:** Click "View Source" to show the cited excerpt from the official PSREF.
4. **Human Approval Demonstration [S19]:**
   - Click **"Mock Cart"** tab: Prove the cart is currently **0 items** (cart is unchanged before approval).
   - Return to Check tab and click **"Review Cart Proposal"**.
   - Show the Approval Modal displaying: Proposed SKU `RAM-A`, Price `$42.99`, Qty `1`, and Agent Rationale.
   - Click **"Approve & Add to Cart"**.
   - The Independent Verifier confirms: `VERIFIED` — 1x `RAM-A` in remote cart.
   - Click the button again to prove **idempotency**: no duplicate items are added.

---

### Step 3: Official TC2 — Conflicting Manufacturer Sources [S21]
1. Click **"TC2: Conflicting Sources"**.
   - Input: Model `DEMO-LAPTOP-002`, Part `RAM`.
2. Click **"Verify Technical Compatibility"**.
3. **Show the Judge:**
   - **Verdict Banner:** `UNCERTAIN` (Amber).
   - **Explanation:** PSREF Specification Sheet asserts `DDR4`, while Global Technical Support Bulletin asserts `DDR5`.
   - **Agent Integrity:** The agent **refuses to guess** or silently pick one source.
   - **Cart State:** Cart proposal is strictly **BLOCKED**. No cart mutation occurred.

---

### Step 4: Official TC3 — Ambiguous Model & Clarify Resume [S22]
1. Click **"TC3: Ambiguous Model"**.
   - Input: `Dell laptop`.
2. Click **"Verify Technical Compatibility"**.
3. **Show the Judge:**
   - **Verdict Banner:** `MORE_INFO_REQUIRED` (Indigo).
   - **Agent Guidance:** Informs the user that "Dell laptop" is a family name, explains why specs cannot be inferred, and tells them where to find the 7-character Service Tag (chassis bottom, BIOS F2).
4. **Clarification Resume:**
   - In the clarification box, enter `DEMO-LAPTOP-001`.
   - Click **"Submit Model Details"**.
   - The agent resumes the exact same session and transitions to `COMPATIBLE`.

---

### Step 5: Official TC4 — Unsupported Universal Claim [S23]
1. Click **"TC4: Universal Claim"**.
   - Input: `DEMO-LAPTOP-004` (65W USB-C laptop) + Candidate `UNIVERSAL-CHARGER-001`.
2. Click **"Verify Technical Compatibility"**.
3. **Show the Judge:**
   - **Verdict Banner:** `NOT_TRUSTED` (Orange).
   - **Explanation:** Product listing says "works with all laptops" but omits voltage steps, pinouts, and USB Power Delivery (PD) negotiation protocols.
   - **Cart State:** Cart mutation is **BLOCKED**.

---

### Step 6: One-Click Automated Test Dashboard [S25]
1. Click the **"Test Dashboard"** tab.
2. Click **"Run All Official Tests"**.
3. Watch the automated runner execute all 4 official tests live against the backend API and remote Mock Store.
4. Point out the live assertion logs, millisecond latency measurements, and the dynamic `ALL_PASSED` badge. **No hardcoded PASS**.

---

### Step 7: Security & Settings Inspection
1. Click the **"API & System"** tab.
2. Show the judge that all three required API keys (Gemini, Search Provider, Product Details) are **masked** (`AIza****...`), stored exclusively server-side, and never exposed in the browser bundle or Git repository.
