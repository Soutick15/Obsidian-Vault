================================================================================
05_COMPLIANCE-AI FORENSIC ANALYSIS
SERVICE: compliance-ai
DATABASE: compliance_dev (PostgreSQL) - Shared with Core and Auth
FRAMEWORK: Quarkus 3.30.6
================================================================================

================================================================================
## 1. SERVICE OVERVIEW
================================================================================

PURPOSE:
The AI brain of the ComplianceManagementSystem compliance ecosystem. It offloads expensive or complex
Large Language Model (LLM) operations and semantic evaluations from `compliance-core`.
It relies on the shared `compliance_dev` database to read entity configurations,
tasks, and tenant settings.

BUSINESS RESPONSIBILITY:
- AI-driven auto-assignment of Acts to specific Departments based on Entity Profile.
- Semantic Gap Analysis comparing imported obligations against existing tasks.
- Intelligent Evidence Ranking (matching uploaded documents to compliance tasks).
- Auto-assignment of high-confidence evidence to task instances.
- Processing Questionnaire responses into LLM summaries.

WHY THIS SERVICE EXISTS:
LLM calls are notoriously slow, prone to rate limits, and failure-prone. Isolating
this logic into a dedicated microservice prevents AI bottlenecks from degrading
the performance of the primary CRUD application (`compliance-core`). It relies
heavily on Quartz Schedulers (`@Scheduled`) to run these evaluations asynchronously
in the background.

================================================================================
## 2. KEY SCHEDULERS & WORKFLOWS
================================================================================

### 2.1 AiAutoAssignScheduler
Evidence: scheduler/AiAutoAssignScheduler.java
- Trigger: Background cron job (`@Scheduled`).
- Purpose: When a tenant onboarding profile is updated, it determines which Acts apply.
- Flow:
  1. Checks `TenantSetting` to see if AI Auto-Assign is enabled. If not, falls back
     to a synchronous Rule Engine in `compliance-core` via REST client.
  2. Extracts the Business Entity description or Questionnaire Profile Summary.
  3. Uses LLM to rank applicability of available Acts against the entity.
  4. If Acts match above a confidence threshold (e.g., 0.7), it maps the Acts to
     the entity.
  5. Further distributes Acts down to specific Departments using LLM batch scoring.

### 2.2 AiEvidenceAutoAssignScheduler
Evidence: scheduler/AiEvidenceAutoAssignScheduler.java
- Trigger: `@Scheduled(cron = "${ai.evidence.auto-assign.cron}")`.
- Purpose: Periodically links uploaded evidence (files/documents) to active task instances.
- Flow:
  1. Scans tenants where `llm_evidence_auto_assign` is enabled.
  2. Limits concurrent processing to protect DB/LLM using a `Semaphore`.
  3. Uses `AiEvidenceSuggestionService` to identify high-confidence matches.
  4. Automatically attaches the evidence to the task, saving the SME manual review time.

================================================================================
## 3. KEY SERVICES (LLM INTEGRATION)
================================================================================

### 3.1 ClaudeRankingService
Evidence: service/ClaudeRankingService.java
- Architecture Decision: DOES NOT USE VECTOR EMBEDDINGS (RAG).
- Why?: Vector similarity (Cosine distance) often fails on compliance nuances (e.g.,
  "PF Challan March 2025" vs "PF Challan April 2025").
- Instead: It sends ONLY document metadata (extracted summaries, keywords, doc type, dates)
  to Claude in a single prompt.
- Cost/Security: 200-300 characters per document are sent, NOT the raw 500KB PDF.
  Saves token costs and prevents exposing sensitive PII/financial data in the raw PDF.

### 3.2 GapAnalysisService
Evidence: service/GapAnalysisService.java
- Purpose: When a tenant imports a list of obligations (e.g., from an audit or Excel),
  this service semantically compares them against the existing tasks in `compliance_dev`.
- Outputs 3 Match Types:
  - `MATCHED_ENABLED`: Obligation is already handled by an active task.
  - `MATCHED_DISABLED`: Handled by a disabled task.
  - `NOT_MATCHED`: A genuine compliance gap; no task exists for this obligation.
- Technique: Batches obligations (e.g., 50 at a time) to avoid LLM token limits (200k max).

================================================================================
## 4. INTEGRATIONS & CONFIGURATION
================================================================================

### 4.1 REST Clients
Evidence: application-dev.properties
- `evidence-service`: Connects to `http://localhost:8087` (another microservice we
  haven't fully analyzed yet, but implies document storage/OCR).
- `ComplianceProfileClient`: Calls `compliance-core` to get questionnaire profiles.
- `ComplianceServiceRuleEngineClient`: Triggers deterministic rules if AI is off.

### 4.2 Database Access
- Uses `jdbc:postgresql://.../compliance_dev`.
- `quarkus.hibernate-orm.database.generation=none`: Explicitly relies on
  `compliance-initial-data` (Flyway) for schema generation.

================================================================================
## 5. INTERVIEW DISCUSSION POINTS (SYSTEM DESIGN)
================================================================================

Q: How do you prevent LLM latency from impacting user experience?
A: We architected `compliance-ai` as an asynchronous, event/scheduler-driven service.
   When a user uploads a document or completes a profile, we immediately return a
   success response (HTTP 202 or 200 marking 'pending'). Schedulers like
   `AiAutoAssignScheduler` and `AiEvidenceAutoAssignScheduler` pick up the work
   in the background, process it via LLM, and update the shared database.

Q: How do you handle evidence matching securely without sending raw sensitive PDFs to OpenAI/Anthropic?
A: We implemented a Metadata-Only Ranking System (`ClaudeRankingService`). A separate
   pipeline (likely `evidence-service`) extracts non-sensitive keywords, dates, and
   a 2-line summary using local tools or sanitized OCR. We send only this metadata
   (about 300 chars per doc) to the LLM. The LLM ranks the candidates and returns
   a JSON array of scores. This ensures PII is never sent to third-party LLMs and
   keeps token costs near zero.

Q: Why didn't you use Vector Search (RAG) for matching tasks to documents?
A: In compliance, "PF Challan 2024" and "PF Challan 2025" are semantically identical
   in vector space, but completely different contextually for a task due date.
   By passing the explicit task requirements and document metadata directly to the
   LLM prompt, the LLM can apply logical reasoning (e.g., "Does the document date
   fall within the task period?") which vector cosine-similarity cannot do reliably.

================================================================================
END OF COMPLIANCE-AI ANALYSIS
================================================================================
