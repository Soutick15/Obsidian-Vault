================================================================================
04_MDM-SUBSCRIPTIONS FORENSIC ANALYSIS
SERVICE: mdm-subscriptions
DATABASE: mdm_dev (PostgreSQL) - Shared/Connected with MDM Core
FRAMEWORK: Quarkus 3.30.6
================================================================================

================================================================================
## 1. SERVICE OVERVIEW
================================================================================

PURPOSE:
The synchronization broker between the global Master Data Management (MDM) repository
and individual tenant compliance systems (`compliance-core`). It manages the initial
bulk onboarding of data (Snapshots) and the continuous replication of regulatory
updates (Change Logs) via a cursor-based chunked streaming architecture.

BUSINESS RESPONSIBILITY:
- Manage tenant subscriptions to specific legal domains/Acts.
- Generate Snapshot Jobs (initial bulk sync) for newly onboarded tenants.
- Generate Change Jobs (delta sync) by trailing the MDM `change_logs` table.
- Provide chunked payload retrieval for `compliance-core` to pull data reliably.
- Auto-discover and assign relevant Acts to tenants based on their entity profile.

WHY THIS SERVICE EXISTS:
Data isolation and resilience. Tens of thousands of tenants cannot poll the central
MDM database directly. `mdm-subscriptions` acts as an asynchronous job manager that
slices data into consumable JSON chunks, calculates MD5 checksums, and manages
sequence cursors per tenant, ensuring exactly-once data delivery.

================================================================================
## 2. ARCHITECTURE & WORKFLOW
================================================================================

### 2.1 The Two Modes of Synchronization
1. SNAPSHOT MODE (Initial Onboarding):
   - When a tenant subscribes to an Act, a `SnapshotJob` is created.
   - `SnapshotWorker` processes the job in the background, querying `mdm_db` for
     all Acts, Rules, Regulations, Provisions, and Obligations.
   - Data is sliced into `SnapshotChunk` rows.
   - The tenant system pulls chunks sequentially.

2. CHANGE MODE (Delta Updates):
   - MDM Core generates a `ChangeLog` row whenever a SME edits a law.
   - `ChangeJobWorker` runs every 5 minutes and queries if the tenant's
     `SubscriptionCursor.lastAckedSequence` is behind the latest `ChangeLog`.
   - If behind, a `ChangeJob` is created, slicing the deltas into `ChangeChunk`s.
   - The tenant pulls these updates to apply the deltas locally.

### 2.2 Intelligent Auto-Assignment
The tenant passes their "Entity Profile" (industry type, employee count, operations)
to MDM. The `ActAutoAssignmentWorker` runs periodically to execute the
`ActAutoAssignmentService`. This service matches the tenant's profile against the
Applicability profiles of Acts (likely using LLM/Rules) and auto-assigns matching
legislation to their subscription, triggering a Snapshot.

================================================================================
## 3. PACKAGE & COMPONENT ANALYSIS
================================================================================

### Workers (com.nyai.mdm.subscription.worker)
- `SnapshotWorker` (@Scheduled every 1m): Picks up pending SnapshotJobs and generates chunks.
- `ChangeJobWorker` (@Scheduled every 5m): Evaluates subscriptions against new `change_logs`.
- `ActAutoAssignmentWorker` (@Scheduled every 5m): Checks if subscriptions have the flag
  `evaluation_pending = true`. Runs the discovery engine and updates the `tenant_act_assignments`.
- `SubscriptionReconcilerWorker`: Reconciles entity-level subscriptions.

### Controllers (com.nyai.mdm.subscription.controller)
Evidence: controller/SubscriptionController.java
- `GET /subscription/jobs?type=SNAPSHOT|CHANGE` — Ask MDM for pending sync jobs.
- `GET /subscription/jobs/{jobId}/chunks/{chunkNumber}` — Download the chunk payload.
- `POST /subscription/jobs/{jobId}/consume` — Acknowledge job completion, advancing the cursor.
- `PUT /subscription/status` — Submit entity profile for Act Discovery.
- `POST /subscription/imported-acts/sync` — Normalize and map Excel uploads from tenants
   into formal MDM Act subscriptions.

### Services (com.nyai.mdm.subscription.serviceimpl)
- `ChangeJobServiceImpl.java`: Handles cursor math, queries `changeLogRepository`,
  slices data into chunks of size 20, applies MD5 hashing, saves to `ChangeChunk`.
- `SnapshotJobManager.java`: Extracts job state transitions using `REQUIRES_NEW`
  transactions to prevent long-running snapshot locks from rolling back on chunk failure.

================================================================================
## 4. DATABASE PATTERNS
================================================================================

TABLES MANAGED BY THIS SERVICE:
- `subscriptions` — Tenant's state (`onboardingStatus`).
- `subscription_cursors` — Tracks the `lastAckedSequence` for delta sync.
- `snapshot_jobs` / `snapshot_chunks` — Ephemeral bulk payload tables.
- `change_jobs` / `change_chunks` — Ephemeral delta payload tables.

DESIGN CHOICE: CHUNKING
- Why?: Instead of a single massive JSON payload, data is saved as chunk rows with
  `chunk_number`, `total_chunks`, and `checksum`. This allows the client to retry
  specific chunks if the network drops, preventing Out-Of-Memory (OOM) errors on
  both sides.

================================================================================
## 5. INTERVIEW DISCUSSION POINTS (SYSTEM DESIGN)
================================================================================

Q: How do you handle data replication between a central Master database and thousands of tenant databases?
A: We implemented a Cursor-Based Chunked Replication system.
   1. The MDM writes changes to an append-only `change_logs` table with a sequential ID.
   2. `mdm-subscriptions` maintains a `SubscriptionCursor` for each tenant.
   3. A background worker periodically finds tenants lagging behind the head sequence.
   4. It packages the deltas into a `ChangeJob` broken into 20-record chunks.
   5. The tenant pulls the chunks, verifies the MD5 checksum, applies the changes locally,
      and calls `/consume` to advance their cursor.
   This guarantees exactly-once delivery, allows tenants to sync at their own pace,
   and prevents massive memory spikes.

Q: What happens if the payload is huge during an initial onboarding?
A: We use a separate `SnapshotWorker`. Initial data is not sent as a change log.
   It creates a `SnapshotJob`, does a full export of the assigned Acts into `SnapshotChunk`s,
   and the tenant downloads these chunks sequentially. Only after the snapshot finishes
   does the delta cursor activate.

Q: How do you handle intelligent onboarding?
A: We use an `ActAutoAssignmentWorker` with an optimistic locking mechanism (`last_updated`).
   The tenant uploads an Entity Profile JSON. The worker uses `ActAutoAssignmentService`
   to rule-match the profile against Acts. To handle concurrent profile updates during
   evaluation, it snapshots the `last_updated` timestamp, and if it drifted during the job,
   it leaves `evaluation_pending = true` to force a re-run on the next tick.

================================================================================
END OF MDM-SUBSCRIPTIONS ANALYSIS
================================================================================
