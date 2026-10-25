# TechFit Agent — AI-Powered RAM & Charger Compatibility Checker

[![Tests](https://img.shields.io/badge/pytest-28%20passed-brightgreen.svg)](#automated-testing)
[![Architecture](https://img.shields.io/badge/Architecture-Deterministic%20Rule%20Engine%20%2B%20LLM%20Orchestrator-blue.svg)](#architecture)
[![Render Blueprint](https://img.shields.io/badge/Deploy%20on-Render-46E3B7.svg)](#live-deployment-on-render)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](LICENSE)

> **TechFit Agent** is a production-grade, autonomous AI agent that verifies whether replacement **RAM** or a **Laptop Charger** is physically and electrically compatible with a user's exact device before purchase.
>
> Built for the official **AI Product Compatibility Checker Agent Hackathon** following all 29 specification slides (`Product_Compatibility_Checker_Black_White.pptx` [S1–S29]).

---

## Table of Contents
1. [Core Features & Innovation](#core-features--innovation)
2. [Architecture & System Design](#architecture--system-design)
3. [The 3 External API Keys](#the-3-external-api-keys)
4. [Official Test Cases (TC1 – TC4)](#official-test-cases-tc1--tc4)
5. [Local Quickstart Guide](#local-quickstart-guide)
6. [Automated Testing Suite](#automated-testing-suite)
7. [Live Deployment on Render (`render.yaml`)](#live-deployment-on-render)
8. [Cold-Start & Performance Handling](#cold-start--performance-handling)
9. [Project Directory Layout](#project-directory-layout)
10. [REST API Documentation](#rest-api-documentation)

---

## Core Features & Innovation

- **Deterministic Rule Engine (No Hallucinations)**: The LLM parses user queries, extracts specifications, and synthesizes human explanations; **pure, deterministic Python functions** compute compatibility verdicts (`COMPATIBLE`, `INCOMPATIBLE`, `UNCERTAIN`, `MORE_INFO_REQUIRED`, `NOT_TRUSTED`).
- **Real Manufacturer Specification Retrieval**: Live search over official OEM specification sheets (Lenovo PSREF, Dell Support, Apple Specs, HP Whitepapers) via Serper / SerpApi / Google Search.
- **Traceable Provenance & Citations**: Every technical claim is anchored by source title, URL, reliability tier, and verified quote excerpts.
- **Strict Human Approval Gate**: The AI agent **cannot** mutate shopping carts autonomously. When a product is verified compatible, it generates a proposal requiring explicit user approval.
- **Independent Cart Verifier**: The system verifies cart operations by querying the isolated mock shopping store directly, avoiding blind trust in agent memory.
- **End-to-End Audit Trail**: Complete session timeline, raw LLM tool calls, retrieved payloads, and decision matrices persisted in PostgreSQL / SQLite.
- **Multi-Service Monorepo**: Decoupled React 19 Frontend (`apps/web`), FastAPI Backend Agent (`apps/api`), and Independent Mock Store (`apps/mock_store`).

---

## Architecture & System Design

```
+---------------------------------------------------------------------------------------+
|                                    USER INTERFACE                                     |
|                       React 19 + TypeScript + Vite + Tailwind CSS                      |
|           [Check Wizard]  [Live Timeline]  [Comparison Table]  [Approval Modal]       |
+------------------------------------------+--------------------------------------------+
                                           | HTTP / REST
+------------------------------------------v--------------------------------------------+
|                             TECHFIT AGENT API (FastAPI)                               |
|                                                                                       |
|   1. Intent Parsing       2. Safe Retrieval       3. Extraction & Normalization       |
|      (Gemini LLM)         (Serper / SerpApi)       (Pydantic Schema Validation)       |
|                                                                                       |
|   4. Deterministic Rule Engine                    5. Audit Trail & Citations          |
|      - RAM: DDR, Form Factor, Slots, Max Cap         - URL Provenance                 |
|      - Charger: Voltage, Wattage, USB-C PD           - Excerpt Guard                  |
|                                                                                       |
|   6. Human Approval Orchestration                 7. Independent Cart Verifier        |
|      - Signed Proposals                              - Direct Mock Store Query        |
|      - Idempotency & Tamper Defense                  - Cross-Check Verified State     |
+---------------------+-------------------------------------+---------------------------+
                      |                                     |
       Bearer Token + |                                     | Async SQLAlchemy
      Idempotency Key |                                     |
+---------------------v----------------+   +----------------v---------------------------+
|     INDEPENDENT MOCK STORE           |   |       MANAGED POSTGRESQL / SQLITE          |
|    Isolated FastAPI Microservice     |   |                                            |
|   - Product Catalog (/store/products)|   |   - Device Specs & Seed Fixtures           |
|   - Authenticated Cart State         |   |   - Audit Logs & Timeline Events           |
|   - Idempotent Cart Mutation         |   |   - Cart Proposals & Verifications         |
+--------------------------------------+   +--------------------------------------------+
```

---

## The 3 External API Keys

TechFit requires three API keys. **All keys reside strictly server-side** in `.env` (local) or Render Secret Environment Variables (production). Raw keys are never logged, returned in API responses, or bundled into frontend assets.

| # | Purpose | Environment Variable | Provider / Link to Obtain |
|---|---|---|---|
| **1** | **Web Search API**<br>Finds official manufacturer support and spec pages | `SEARCH_API_KEY`<br>`SEARCH_PROVIDER=serper` | [Serper.dev](https://serper.dev) (2,500 free queries, no card) or [SerpApi](https://serpapi.com) |
| **2** | **Gemini LLM API**<br>Intent parsing, structured extraction, explanation | `GEMINI_API_KEY`<br>`GEMINI_MODEL=gemini-3.5-flash` | [Google AI Studio](https://aistudio.google.com/apikey) |
| **3** | **Product Details API**<br>Enriches candidate product specs and listings | `PRODUCT_DETAILS_API_KEY`<br>`PRODUCT_DETAILS_PROVIDER=serpapi` | [SerpApi](https://serpapi.com) (100 free searches/mo) or Mock Catalog fallback |

> **Security Note:** The status of these keys can be inspected safely via the authenticated `/api/admin/config-status` endpoint or the **Settings** view in the UI, which displays masked values (e.g. `AQ.A****8Q`) and smoke test verdicts.

---

## Official Test Cases (TC1 – TC4)

All four mandatory test cases from the hackathon brief ([S21–S24]) are verified by the automated test suite and executable via the frontend Test Dashboard:

| Test ID | Device Under Test | Candidate Product / Input | Expected Verdict | Actual Verdict | Result |
|---|---|---|---|---|---|
| **TC1** | **Lenovo ThinkPad T480** | Crucial 16GB DDR4 2666MHz SO-DIMM (`RAM-DDR4-16G-001`) | `COMPATIBLE` | `COMPATIBLE` | **PASS** |
| **TC2** | **Dell Inspiron 15 5570** | Crucial 32GB DDR4 Kit (Conflicting manual: 16GB vs Crucial 32GB) | `UNCERTAIN` | `UNCERTAIN` | **PASS** |
| **TC3** | **Dell Laptop** (Ambiguous) | Missing model name -> Resumed with *"Dell XPS 15 9570"* | `MORE_INFO_REQUIRED` &rarr; `COMPATIBLE` | `MORE_INFO_REQUIRED` &rarr; `COMPATIBLE` | **PASS** |
| **TC4** | **Asus ROG Zephyrus G14** | *"Universal 65W Laptop Charger"* (`UNIVERSAL-CHARGER-001`) | `NOT_TRUSTED` | `NOT_TRUSTED` | **PASS** |

---

## Local Quickstart Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Clone & Environment Setup
```bash
git clone <repository-url>
cd "TechFit Agent — AI-Powered RAM & Charger Compatibility Checker"

# Copy environment template
cp .env.example .env
```

Edit `.env` and fill in your three keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
SEARCH_PROVIDER=serper
SEARCH_API_KEY=your_serper_api_key_here
PRODUCT_DETAILS_PROVIDER=serpapi
PRODUCT_DETAILS_API_KEY=your_serpapi_key_here
```

### 2. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd apps/web
npm install
cd ../..
```

### 3. Initialize & Seed Databases
```bash
# Seed Backend Database (Devices & Fixtures)
python -m apps.api.seed

# Seed Mock Store Database (Store Catalog & Carts)
python -m apps.mock_store.seed
```

### 4. Run Services Concurrently

Open three terminal windows (or tabs):

```bash
# Terminal 1: Independent Mock Store (Port 8001)
uvicorn apps.mock_store.main:app --port 8001 --reload

# Terminal 2: TechFit Agent Backend API (Port 8000)
uvicorn apps.api.main:app --port 8000 --reload

# Terminal 3: React Web Frontend (Port 5173)
cd apps/web
npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

## Automated Testing Suite

The repository contains an exhaustive test suite covering unit rules, contract endpoints, mock store integration, LLM agent functions, and security guards:

### 1. Run Complete Test Suite
```bash
python -m pytest tests/ -v
```
Output:
```
tests/test_contracts.py::test_healthz_endpoint PASSED                    [  3%]
tests/test_contracts.py::test_admin_config_status_endpoint PASSED        [  7%]
tests/test_contracts.py::test_products_endpoint PASSED                   [ 10%]
tests/test_contracts.py::test_test_dashboard_runner_endpoint PASSED      [ 14%]
tests/test_mock_store.py::test_mock_store_health PASSED                  [ 17%]
tests/test_mock_store.py::test_mock_store_products_listing PASSED        [ 21%]
tests/test_mock_store.py::test_mock_store_token_authentication PASSED    [ 25%]
tests/test_mock_store.py::test_mock_store_idempotent_cart_addition PASSED [ 28%]
tests/test_official_fixtures.py::test_tc1_ddr4_laptop_e2e PASSED         [ 32%]
tests/test_official_fixtures.py::test_tc2_conflicting_sources PASSED     [ 35%]
tests/test_official_fixtures.py::test_tc3_unknown_model_and_resume PASSED [ 39%]
tests/test_official_fixtures.py::test_tc4_unsupported_universal_claim PASSED [ 42%]
tests/test_phase3_agent.py::test_llm_intent_parsing PASSED               [ 46%]
tests/test_phase3_agent.py::test_search_provider_live_retrieval PASSED   [ 50%]
tests/test_phase3_agent.py::test_provenance_excerpt_verification_guard PASSED [ 53%]
tests/test_phase3_agent.py::test_prompt_injection_defense PASSED         [ 57%]
tests/test_rules_charger.py::test_charger_unsupported_universal_claim PASSED [ 60%]
tests/test_rules_charger.py::test_charger_exact_match_usb_c_pd PASSED    [ 64%]
tests/test_rules_charger.py::test_charger_voltage_mismatch PASSED        [ 67%]
tests/test_rules_charger.py::test_charger_insufficient_wattage PASSED    [ 71%]
tests/test_rules_ram.py::test_ram_rule_exact_match PASSED                [ 75%]
tests/test_rules_ram.py::test_ram_rule_ddr_mismatch PASSED               [ 78%]
tests/test_rules_ram.py::test_ram_rule_form_factor_mismatch PASSED       [ 82%]
tests/test_rules_ram.py::test_ram_rule_soldered_zero_slots PASSED        [ 85%]
tests/test_rules_ram.py::test_ram_rule_capacity_exceeded PASSED          [ 89%]
tests/test_security.py::test_security_prevent_altered_approved_sku PASSED [ 92%]
tests/test_security.py::test_security_prevent_cart_mutation_for_incompatible_product PASSED [ 96%]
tests/test_security.py::test_security_no_secret_leaks_in_responses PASSED [100%]
======================== 28 passed, 1 warning in 8.55s ========================
```

### 2. Run Pre-Commit Secret Scanner
Scans all tracked files, documentation, and commits to verify zero API keys or secrets are committed:
```bash
python scripts/scan_secrets.py
```

### 3. Run Real Public-Source Verification
Executes live search queries against official OEM pages using the configured search provider:
```bash
python scripts/verify_real_sources.py
```

### 4. Run End-to-End Headless Browser Verification
Launches a headless browser session to simulate user interaction and capture UI screenshots in `docs/screenshots/`:
```bash
python scripts/test_ui_e2e.py
```

---

## Live Deployment on Render

The repository includes a declarative **Render Blueprint** (`render.yaml`) that deploys all four components in one step:
1. `techfit-web`: Static Site serving the compiled React frontend.
2. `techfit-api`: Python Web Service running the Agent orchestrator and rule engine.
3. `techfit-mock-store`: Python Web Service running the isolated mock store.
4. `techfit-db`: Render Managed PostgreSQL instance.

### Step-by-Step Deployment Instructions

1. **Push your repository to GitHub / GitLab**.
2. **Log in to [Render Dashboard](https://dashboard.render.com/)**.
3. Click **New +** &rarr; Select **Blueprint**.
4. Connect your repository and select the `master` (or `main`) branch. Render will detect `render.yaml`.
5. Render will show the four resources to be created.
6. Provide the values for the secrets declared with `sync: false`:
   - `GEMINI_API_KEY`: Your Gemini API key from Google AI Studio.
   - `SEARCH_API_KEY`: Your Serper or SerpApi API key.
   - `PRODUCT_DETAILS_API_KEY`: Your SerpApi API key.
   - `MOCK_STORE_SERVICE_TOKEN`: A strong random string (e.g., `techfit_sec_token_a984b2c1f0e478d1`).
   - `ADMIN_API_KEY`: A strong random string for admin access (e.g., `techfit_admin_secret_4892bc01ef3a7719`).
7. Click **Apply**.
8. Render will provision the PostgreSQL database, build the mock store, build the backend API, and compile the frontend static site.
9. Verify health checks at:
   - `https://<techfit-api>.onrender.com/healthz`
   - `https://<techfit-mock-store>.onrender.com/healthz`

---

## Cold-Start & Performance Handling

When running on Render free-tier instances:
- Free services sleep after 15 minutes of inactivity and take **30 to 50 seconds** to wake on the next incoming request.
- **Frontend Cold-Start Banner**: The React frontend features a dedicated cold-start detection mechanism with an animated status indicator and an automatic retry loop, ensuring the user is never left with a blank or broken screen.
- **Recommendation for Demo Day**: We recommend upgrading the `techfit-api` and `techfit-mock-store` services to the Render Starter instance ($7/month) during live presentations to eliminate spin-down latency.

---

## Project Directory Layout

```
.
|-- .env.example                       # Documented environment template
|-- .gitignore                         # Strict exclusion rules (secrets, DBs, node_modules)
|-- README.md                          # Production documentation
|-- PROGRESS.md                        # Phase-by-phase implementation log
|-- render.yaml                        # Render Blueprint multi-service deployment
|-- requirements.txt                   # Production Python dependencies
|-- apps/
|   |-- api/                           # TechFit Agent Backend Service
|   |   |-- config.py                  # Pydantic Settings
|   |   |-- database.py                # Async SQLAlchemy engine
|   |   |-- models.py                  # DB Entities (Checks, Audits, Proposals)
|   |   |-- seed.py                    # Device specs & test fixtures
|   |   |-- main.py                    # FastAPI application entrypoint
|   |   |-- routers/                   # REST Endpoints (checks, cart, admin, tests)
|   |   `-- services/
|   |       |-- rule_engine/           # Deterministic RAM & Charger rule engines
|   |       |-- retrieval/             # Search providers, fetcher, product enrichment
|   |       |-- agent/                 # Gemini LLM client, intent parser, prompt guards
|   |       `-- verifier.py            # Independent mock store cart verifier
|   |-- mock_store/                    # Independent Mock Shopping Store
|   |   |-- main.py                    # Store API & Cart routes
|   |   |-- models.py                  # Store Products & Carts
|   |   `-- seed.py                    # Store catalog seeder
|   `-- web/                           # React 19 + TypeScript + Tailwind Frontend
|       |-- src/
|       |   |-- components/            # Wizard, Timeline, Tables, Modals, Banner
|       |   |-- api.ts                 # Type-safe API client
|       |   `-- types.ts               # Shared domain interfaces
|       |-- package.json
|       `-- vite.config.ts
|-- docs/
|   |-- API.md                         # Exhaustive REST API specification
|   |-- DECISIONS.md                   # Architecture Decision Records (ADRs)
|   |-- DEMO_SCRIPT.md                 # 5-minute hackathon presentation script
|   `-- screenshots/                   # Automated E2E browser screenshots
|-- packages/
|   `-- shared_schemas/                # Pydantic schemas shared across services
|-- scripts/
|   |-- scan_secrets.py                # Pre-commit secret scanning script
|   |-- smoke_test_keys.py             # Key onboarding verification harness
|   |-- test_ui_e2e.py                 # Headless Playwright browser E2E test
|   `-- verify_real_sources.py         # Real OEM public spec verification script
`-- tests/                             # 28 Pytest automated test suites
```

---

## REST API Documentation

For the complete REST API specification—including all endpoints, request/response JSON schemas, error codes, and curl examples—see **[`docs/API.md`](docs/API.md)**.
