# TechFit Architecture & Engineering Decisions (ADR)

## ADR 001: Monorepo Structure & Technology Stack

### Context
The hackathon specification requires an agentic AI application that performs exact laptop RAM and charger compatibility checks. The solution must feature a frontend UI, backend agent orchestrator, rule engine, mock shopping store, database audit trail, and reproducible test suite. Optional tools proposed by organizers are superseded by a robust, maintainable production architecture.

### Decision
We select a modern typed monorepo:
1. **Frontend (`apps/web`)**:
   - **Framework**: React 18 / 19 + TypeScript + Vite. Fast compilation, zero-bloat runtime.
   - **Styling**: Tailwind CSS for responsive, accessible, clean UI.
   - **State & Server Cache**: TanStack Query (React Query) for robust data fetching, caching, loading states, and cold-start retries.
   - **Routing**: React Router for seamless navigation across Check, Reports, Cart, Tests, History, and Settings.
2. **Backend Agent Orchestrator (`apps/api`)**:
   - **Runtime**: Python 3.11 / 3.12 + FastAPI.
   - **Validation & Typing**: Pydantic v2 for strict type contracts, schema generation, and automatic OpenAPI documentation (`/docs`).
   - **ORM & Migrations**: SQLAlchemy 2 (async) + Alembic for robust transactional data integrity and database schema migrations.
   - **HTTP Client**: `httpx` (async) for manufacturer page retrieval, search queries, and external APIs.
   - **Logging**: Structured JSON logging with request tracing and correlation IDs.
3. **Mock Shopping Store (`apps/mock-store`)**:
   - A standalone FastAPI service with its own isolated database tables for products, inventory, and cart sessions.
   - Guarded with `MOCK_STORE_SERVICE_TOKEN` bearer authorization.
   - This ensures the independent verifier checks true store state rather than the agent's internal memory.
4. **Database**:
   - PostgreSQL (production on Render).
   - SQLite (`sqlite+aiosqlite`) fallback for instant zero-dependency local test execution.

---

## ADR 002: Render Deployment Blueprint (`render.yaml`)

### Context
Requirement A1 demands live deployment on Render (render.com) using an infrastructure-as-code `render.yaml` Blueprint.

### Decision
- **Services in `render.yaml`**:
  1. `techfit-web`: Static Site building `apps/web` (or Web Service).
  2. `techfit-api`: Web Service running `apps/api` (Uvicorn).
  3. `techfit-mock-store`: Web Service running `apps/mock-store` (Uvicorn).
  4. `techfit-db`: Managed PostgreSQL database.
- **Health Checks**: Every service exposes `/healthz` returning `{"status": "ok", "service": "..."}`.
- **Cold-Start Handling**: Render free-tier instances sleep after 15 minutes of inactivity. The frontend includes a dedicated ping/wake-up mechanism with friendly UI countdowns and retries rather than blank errors.
- **Secrets Management**: Marked `sync: false` in `render.yaml`. No secrets are committed to git.

---

## ADR 003: Search Provider & Google Custom Search Route Evaluation

### Context
Requirement A2.2 mandates verifying the current state of the Google Search route before building on it. Google's Custom Search JSON API was evaluated against current documentation.

### Findings
1. **Google Custom Search JSON API Deprecation**:
   - Google has officially announced that the Custom Search JSON API is closed to new customers and scheduled for final discontinuation on **January 1, 2027**.
   - Programmable Search Engines configured for "Search the entire web" programmatic JSON results are restricted.
   - Google directs enterprise customers to Vertex AI Search (for limited domains) or third-party web search providers.
2. **Evaluation of Alternatives**:
   - **Serper.dev**: Provides 2,500 free Google Search queries upon sign-up, no credit card required, returns structured JSON of live Google Search results with snippet, title, link, and sitelinks.
   - **SerpApi**: Offers 100 free Google searches per month, mature and battle-tested.
   - **Brave Search API**: Provides $5/month in free credits (1,000 queries), requires a card on file.
   - **Google Custom Search (Legacy)**: Supported for developers with an existing Search Engine ID (`cx`) and GCP API key until Jan 1, 2027.

### Decision
We implement a pluggable `SearchProvider` interface with adapters:
- `SerperSearchProvider` (Default recommended: 2,500 free queries, no card required)
- `GoogleCustomSearchProvider` (Compatible with existing GCP `GOOGLE_SEARCH_API_KEY` + `GOOGLE_SEARCH_ENGINE_ID`)
- `SerpApiSearchProvider` (Secondary fallback)
- `MockSearchProvider` (Deterministic offline fixtures for unit/e2e testing)

The provider is selected via `SEARCH_PROVIDER=serper` (or `google_custom_search`).

---

## ADR 004: LLM Client & Strict Architectural Boundary

### Context
The agent requires an LLM for intent extraction, planning, and structured summarization. However, Slide [S8] and [S14] establish a hard architectural constraint:
> "The LLM may plan, extract and explain, but the verdict is computed only by the deterministic rule engine from validated facts. The LLM must never be able to set a verdict, approve an action, or call the cart-mutation tool directly."

### Decision
1. **LLM Implementation**:
   - Official `google-genai` SDK using `gemini-2.5-flash` (or `gemini-1.5-flash` configured via `GEMINI_MODEL`).
   - Abstracted behind an `LLMClient` interface.
   - Uses strict JSON schema structured outputs and function calling with a restricted allow-list.
2. **Untrusted Data Isolation**:
   - Web pages and product descriptions fetched from external URLs are treated as untrusted data.
   - Retrieval prompts sanitize content, isolate raw text in data delimiters (`<document_text>...</document_text>`), and strip simulated tool calls.
3. **Deterministic Verdict Guarantee**:
   - The LLM outputs extracted specification facts with supporting excerpts.
   - The backend validates that excerpts actually exist in the fetched source document.
   - The **Deterministic Rule Engine** evaluates constraints (DDR gen, form factor, voltage, wattage, connector pinout) and outputs the verdict.
   - The LLM generates the human explanation solely based on the rule engine's comparison result table.

---

## ADR 005: Product Details Provider (Key #3)

### Context
Candidate products outside the mock store can be enriched using an external product details provider. Slide [S4] notes no paid shopping APIs are required for the official demo, so this provider must degrade gracefully if absent or rate-limited.

### Evaluated Options
1. **UPCitemdb API**:
   - Free (Explorer) tier: 100 requests/day, 40 search requests/day, 6 req/min rate limit.
   - Self-serve, zero cost.
2. **TrustedParts.com API**:
   - Sponsored by the ECIA (Electronic Components Industry Association).
   - Free developer tier for electronic components, semiconductors, RAM modules, power supplies.
3. **RapidAPI (E-Commerce Product Search)**:
   - Typical free tier: 50–100 requests/month.
4. **Mock Store / Fallback Mode (`mock_store_only`)**:
   - Works immediately with zero external dependencies.

### Decision
We implement the `ProductDetailsProvider` interface:
- Support `upcitemdb` and `trustedparts` adapters.
- If `PRODUCT_DETAILS_API_KEY` is not provided or rate-limited, the system gracefully falls back to the internal mock catalog without crashing.

---

## ADR 006: Human-in-the-Loop Approval & Independent Verification

### Context
Slides [S14], [S18], and [S19] require that cart additions occur ONLY after explicit human approval, and that the cart state is verified independently after mutation.

### Decision
1. **Approval State Machine**:
   - Proposals can only be generated for `COMPATIBLE` verdicts.
   - Each proposal has a cryptographic UUID, timestamp, version, and expiration TTL (15 minutes).
   - Approval payload must match `proposal_id`, `check_id`, `sku`, and `proposal_version`.
   - Mutation requests carry an `idempotency_key` ensuring duplicate requests never add duplicate items.
2. **Independent Verification**:
   - After cart mutation, the verifier queries `GET /api/cart/{cart_id}` on the Mock Store.
   - It asserts the exact SKU and quantity are present.
   - If the Mock Store returns success but the item is absent, the verification state is marked `FAILED`.
