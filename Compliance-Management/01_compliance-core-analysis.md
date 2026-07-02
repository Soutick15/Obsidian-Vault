================================================================================
01_COMPLIANCE-CORE FORENSIC ANALYSIS
SERVICE: compliance-core
PORT: 8080
FRAMEWORK: Quarkus 3.30.6 + Java 21
DATABASE: compliance_dev (Azure PostgreSQL, SHARED with auth/ai)
================================================================================

================================================================================
## 1. SERVICE OVERVIEW
================================================================================

PURPOSE:
The central business logic engine of the NyAi compliance platform. Handles all
tenant-facing compliance management, task lifecycle, entity/department management,
subscription sync with MDM, rule engine evaluation, and data source management.

BUSINESS RESPONSIBILITY:
- Multi-tenant compliance task management (CRUD + lifecycle)
- Task recurrence and instance generation
- Overdue detection and notification
- Rule engine for task applicability evaluation
- MDM subscription sync (pull-based polling)
- Dashboard analytics and metrics
- Evidence management via data sources
- RACI-based task assignment and approval workflows
- Keka HR integration for automated evidence collection
- Questionnaire-driven entity profiling

WHY THIS SERVICE EXISTS:
Separates tenant-facing compliance business logic from authentication (compliance-auth)
and AI intelligence (compliance-ai). Acts as the orchestrator that coordinates between
MDM (legal data) and AI (intelligence) to deliver a complete compliance management experience.

PROBLEM SOLVED:
Automates regulatory compliance tracking for Indian enterprises across multiple business
entities, departments, and legal acts. Replaces manual spreadsheet-based tracking with
automated recurrence, overdue detection, applicability evaluation, and evidence collection.

================================================================================
## 2. PACKAGE ANALYSIS
================================================================================

### Package: com.nyai
- NyaiApplication.java — @QuarkusMain entry point, OpenAPI definition
- Dependencies: Quarkus runtime, MicroProfile OpenAPI

### Package: com.nyai.controller (21 files + 5 subdirs)
PURPOSE: JAX-RS REST endpoints for all tenant-facing APIs
CONTROLLERS:
  - TaskResource.java (25KB) — /v1/core/tasks/** — Largest controller
  - ComplianceResource.java (13KB) — /v1/core/compliances/**
  - EntityResource.java (16KB) — /v1/core/entities/**
  - DepartmentResource.java (11KB) — /v1/core/departments/**
  - DashboardResource.java (10KB) — /v1/core/dashboard/**
  - DataSourceResource.java (11KB) — /v1/core/data-sources/**
  - WorkspaceResource.java (9KB) — /v1/core/workspace/**
  - GapDiscoveryResource.java (9KB) — /v1/core/gap-discovery/**
  - ComplianceScheduleController.java — /v1/core/schedules/**
  - ComplianceProfileController.java — /v1/core/profiles/**
  - ComplianceExistingDataResource.java — /v1/core/existing-data/**
  - KekaSyncController.java — /v1/core/keka/**
  - NotificationResource.java — /v1/core/notifications/**
  - ObligationStagingController.java — /v1/core/obligation-staging/**
  - ReviewResource.java — /v1/core/reviews/**
  - SmtpConfigResource.java — /v1/core/smtp/**
  - TenantSettingsController.java — /v1/core/tenant-settings/**
  - TenantCurrentResource.java — /v1/core/tenant/current
  - PublicSetupResource.java — /v1/core/public/**
  - GenericRestController.java — /v1/core/generic/**
  - QuestionnaireController.java — /v1/core/questionnaire/**

SUBDIRECTORIES:
  - admin/ — TenantManagementResource.java (/v1/core/admin/tenants/**)
  - internal/ — MaterializationInternalController.java, ProfileInternalController.java,
                RuleEngineInternalController.java (internal service-to-service APIs)
  - rule/ — RuleEvaluationController.java (/v1/core/rule-engine/**)
  - settings/ — SettingsController.java
  - subscription/ — UnifiedSubscriptionController.java, SubscriptionCleanupController.java

### Package: com.nyai.entity (58 files)
PURPOSE: JPA entities mapped to PostgreSQL tables
CRITICAL ENTITIES:
  - Task.java (12KB) — Core compliance task with recurrence, JSONB fields
  - TaskInstance.java (5KB) — Concrete instance of a recurring task
  - BusinessEntity.java (7KB) — Company/organization (tenant's business unit)
  - Compliance.java (6KB) — Compliance rule under an Act
  - Act.java (10KB) — Legal act/legislation
  - Obligation.java (7KB) — Legal obligation from MDM
  - Department.java (5KB) — Organizational department
  - User.java (4KB) — System user
  - Tenant.java (2KB) — SaaS tenant
  - Configuration.java (4KB) — RACI and policy configuration
  - DataSource.java (4KB) — External data source connection
  - DataSourceFile.java (3KB) — Uploaded evidence file
  - AuditLog.java (4KB) — Immutable audit trail
  - TaskVersionChangelog.java (6KB) — Task version history
  - MdmTenant.java (4KB) — MDM connection credentials per tenant
  - EntityComputedProfile.java (3KB) — Materialized entity profile fields
  - ApplicabilityEvaluation.java (4KB) — Rule engine evaluation tracking
  - GapDiscoveryLock.java (4KB) — Distributed lock for gap analysis
  - ComplianceExistingData.java (8KB) — Imported legacy compliance data
  - QuestionnaireQuestion.java, QuestionnaireResponse.java, etc. — Questionnaire subsystem

### Package: com.nyai.repository (58 files)
PURPOSE: Panache repositories for database access
CRITICAL:
  - TaskRepository.java (38KB) — Largest repository, complex queries with JPQL/native SQL
  - TaskInstanceRepository.java (50KB) — Complex task instance queries
  - DepartmentRepository.java (6KB) — Department queries with responsibilities JOIN
  - ComplianceRepository.java (6KB) — Compliance CRUD + queries
  - ActRepository.java (7KB) — Act queries with hierarchical structure
  - DepartmentActRepository.java (7KB) — Act-department mapping queries
  - BaseRepository.java (6KB) — Abstract base with common query patterns

### Package: com.nyai.scheduler (9 files)
PURPOSE: Quarkus @Scheduled background jobs
FILES:
  1. SubscriptionSyncScheduler.java — @Scheduled(every="10m") — MDM data sync
  2. SnapshotConsumptionScheduler.java — @Scheduled(every="30s") — Process MDM snapshots
  3. TaskGenerationScheduler.java — @Scheduled(cron="0 0 1 * * ?") — Generate tasks from schedules
  4. TaskRecurrenceScheduler.java — @Scheduled(cron="0 0 1 * * ?") — Create recurring task instances
  5. TaskOverdueScheduler.java — @Scheduled(cron="0 0 0 * * ?") — Mark overdue tasks
  6. TaskReminderScheduler.java — @Scheduled(cron="0 0 9 * * ?") — Morning/evening reminders
  7. TaskStatusUpdateScheduler.java — @Scheduled(cron="0 0 * * * ?") — Auto-update status from action items
  8. RuleEngineMaterializationScheduler.java — @Scheduled(every="5m") [DISABLED] — Rule engine evaluation
  9. LogCleanupScheduler.java — @Scheduled(every="1h") — Purge old application logs

### Package: com.nyai.security (9 files)
PURPOSE: JWT validation, RBAC, request filtering
FILES:
  - CookieAuthRequestFilter.java — @PreMatching filter, extracts JWT from HttpOnly cookie
  - PermissionFilter.java — @AUTHORIZATION filter, path-based RBAC check
  - SecurityUtils.java — User context helper (userId, roles, permissions)
  - RolePermissionConfig.java — Hardcoded role→path→method permission matrix
  - JwtService.java — JWT validation using RSA public key
  - AuthenticatedUser.java — CDI bean holding current user claims
  - PasswordService.java — BCrypt wrapper
  - CookieEntityResolver.java — Resolves entity ID from cookie
  - RequiresPermission.java — Custom annotation (marker)

### Package: com.nyai.client (REST clients)
- ComplianceAiClient.java — @RegisterRestClient for compliance-ai internal API
- SubscriptionClient.java — @RegisterRestClient for mdm-subscriptions
- MdmActClient.java — @RegisterRestClient for mdm-subscriptions act APIs
- OAuthClient.java — OAuth token endpoint client

### Package: com.nyai.service (33 files + 5 subdirs)
PURPOSE: Business logic layer
CRITICAL:
  - TaskService.java — Task CRUD interface
  - MdmClientFactory.java — Dynamic REST client factory (per-tenant MDM URL)
  - MdmTokenService.java — OAuth token caching with ConcurrentHashMap
  - KekaSyncService.java — Keka HR API integration (12 evidence categories)
  - GenericRestSyncService.java — Generic REST API data sync
  - FilterService.java — Cookie/filter resolution
  - NotificationService.java — Email notification dispatch
  - AppNotificationService.java — In-app notification creation

SUBDIRECTORIES:
  - impl/ — Service implementations (TaskServiceImpl, etc.)
  - rule/ — Rule engine logic
  - semantic/ — WordNet-based semantic matching (WordNetService)
  - subscription/ — SnapshotProcessingService, SubscriptionSyncServiceImpl
  - task/ — TaskInstanceMaterializationService

### Package: com.nyai.audit
- EntityAuditObserver.java — CDI @Observes(AFTER_SUCCESS) transactional audit
- EntityAuditEvent.java — CDI event payload

### Package: com.nyai.config, com.nyai.constants, com.nyai.context,
   com.nyai.dto, com.nyai.enums, com.nyai.event, com.nyai.exception,
   com.nyai.logging, com.nyai.util
Standard supporting packages for configuration, DTOs, enums, exceptions, and utilities.

================================================================================
## 3. CONTROLLER ANALYSIS — CRITICAL ENDPOINTS
================================================================================

### TaskResource.java — /v1/core/tasks
Evidence: controller/TaskResource.java

┌──────────────┬──────────┬─────────────────────────────────────┬──────────────────────┐
│ Endpoint     │ Method   │ Purpose                             │ Key Logic            │
├──────────────┼──────────┼─────────────────────────────────────┼──────────────────────┤
│ /            │ POST     │ Create task                         │ filterService.parse  │
│ /            │ GET      │ List tasks by status                │ taskService.getByStatus│
│ /{id}        │ GET      │ Get single task                     │ taskService.getById  │
│ /{id}        │ PUT      │ Update task                         │ taskService.update   │
│ /{id}        │ DELETE   │ Delete task                         │ taskService.delete   │
│ /{id}/action-items │ GET│ Get task action items               │ Sub-entity query     │
│ /{id}/action-items │POST│ Create action item                  │ Nested creation      │
│ /{id}/audit-logs   │GET │ Get audit trail for task            │ AuditLog query       │
│ /{id}/configuration│GET │ Get RACI config                     │ Configuration entity │
│ /{id}/configuration│PUT │ Update RACI config                  │ validateRaciOverlap  │
│ /{id}/legal-frameworks│GET│ Get linked legal frameworks       │ LegalFramework query │
│ /{id}/mark-complete│PUT │ Mark task as complete               │ Status transition    │
│ /{id}/change-assignee│PUT│ Reassign task                     │ RACI validation      │
│ /{id}/severity-penalty│PUT│ Update severity and penalty       │ BigDecimal handling  │
│ /{id}/toggle-active│PUT │ Enable/disable task                 │ Soft delete pattern  │
│ /{id}/instances    │GET │ Get recurring instances             │ TaskInstance query   │
│ /grouped          │GET  │ Grouped task view (Kanban)          │ resolveTaskScope()   │
│ /by-act/{id}      │GET  │ Tasks filtered by act               │ Hierarchical query   │
│ /by-compliance/{id}│GET │ Tasks filtered by compliance        │ Hierarchical query   │
│ /action-items/{id}/complete│PUT│ Complete action item          │ Status update        │
│ /action-items/{id}/toggle-active│PUT│ Toggle action item      │ Soft delete          │
└──────────────┴──────────┴─────────────────────────────────────┴──────────────────────┘

CRITICAL DESIGN: resolveTaskScope() (lines 48-99)
  - 3-tier scope resolution: ADMIN → DEPARTMENT_ADMIN → USER
  - Admin: uses filter entityId OR cookie entityId, resolves tenantId from entity
  - DepartmentAdmin: locked to their department, finds from UserRepository
  - User: uses filter/cookie entityId, no department filter
  - Returns [entityId, departmentId, tenantId] array
  Evidence: TaskResource.java lines 48-99

SECURITY: Every endpoint calls filterService.parseAndResolve(filterJson, cookieHeader)
  This resolves entity context from the JWT cookie before any business logic runs.

### ComplianceResource.java — /v1/core/compliances
Evidence: controller/ComplianceResource.java

Endpoints:
  GET /list — Paginated act listing with search (line 46-79)
  POST / — Create compliance rule (line 81-94)
  GET /{id} — Get compliance by ID (line 96-112)
  PUT /{id} — Update compliance (line 114-129)
  DELETE /{id} — Delete compliance (line 131-141)
  GET /{id}/tasks — List tasks under compliance (line 143-157)
  POST /{id}/tasks — Create task under compliance (line 159-188)
  GET /{id}/audit-logs — Audit trail (line 190-200)
  GET /{id}/configuration — RACI configuration (line 202-214)
  PUT /{id}/configuration — Update RACI (line 216-232)
  GET /{id}/legal-frameworks — Legal frameworks (line 234-246)
  PUT /{id}/mark-complete — Mark complete (line 248-260)
  PUT /{id}/change-owner — Change compliance owner (line 262-277)
  PUT /{id}/toggle-active — Soft enable/disable (line 279-298)
  GET /audit — Audit list with filter (line 300-319)

CRITICAL DESIGN: RACI Overlap Validation
  PUT /{id}/configuration calls taskService.validateRaciOverlap(body)
  This prevents the same user from being both "responsible" and "accountable"
  Evidence: ComplianceResource.java line 222

================================================================================
## 4. SCHEDULER ANALYSIS (DEEP DIVE)
================================================================================

### 4.1 SubscriptionSyncScheduler
FILE: scheduler/SubscriptionSyncScheduler.java
CRON: @Scheduled(every = "10m", identity = "subscription-sync-check")
PURPOSE: Polls MDM for data changes using sequence-number delta sync
FLOW:
  1. Find all MdmTenant records with clientId+clientSecret configured
  2. For each tenant, check if auto-sync is enabled (TenantSetting)
  3. Check configured interval (default 30 min) against last_sync_at
  4. If interval elapsed → call subscriptionSyncService.syncForTenant()
  5. Uses database-persisted last_sync_at (survives restarts, cluster-safe)
FAILURE HANDLING: Per-tenant try/catch, logs error, continues to next tenant
CONCURRENCY: No explicit lock — relies on database timestamp check
INTERVIEW QUESTION: "Why not use Kafka for MDM sync?"
ANSWER: The delta is sequence-number-based. MDM provides a pull API with
  chunked snapshots. Kafka would add infrastructure complexity without benefit
  because the sync is periodic and the volume is manageable.

### 4.2 SnapshotConsumptionScheduler
FILE: scheduler/SnapshotConsumptionScheduler.java
CRON: @Scheduled(every = "30s", identity = "snapshot-consumption-processor")
PURPOSE: Process per-act snapshot jobs from MDM
FLOW:
  1. Wait 90 seconds after startup (STARTUP_DELAY_MS = 90_000)
  2. List all MdmTenant records
  3. For each tenant, call MDM to get pending snapshot jobs
  4. Skip "consumed" or "failed" jobs
  5. Process each job via SnapshotProcessingService
UNIQUE: nodeId = hostname + PID for distributed tracing
  Evidence: line 51: InetAddress.getLocalHost().getHostName() + "_" + ProcessHandle.current().pid()
FAILURE HANDLING: Per-job try/catch, logs error, continues to next job
INTERVIEW QUESTION: "Why the 90-second startup delay?"
ANSWER: Prevents overwhelming MDM API during container restarts/deployments.
  Gives time for database connections and other services to stabilize.

### 4.3 TaskRecurrenceScheduler
FILE: scheduler/TaskRecurrenceScheduler.java
CRON: @Scheduled(cron = "${task.recurrence.cron:0 0 1 * * ?}") — 1 AM daily
PURPOSE: Generate next TaskInstance for recurring tasks
FLOW:
  1. Query tasks: isEnabled=true, recurrenceType != ONE_TIME, nextOccurrenceDate <= now,
     instanceStatus != PENDING_ASSIGNMENT
  2. For each task: create TaskInstance with due date, assigned user, RACI approvers
  3. Update task: increment occurrenceCount, calculate nextOccurrenceDate
  4. Send email notification to RACI users
  5. Send in-app notification to assigned user
RECURRENCE TYPES: ONE_TIME, MONTHLY, QUARTERLY, HALF_YEARLY, YEARLY
DUE DATE CALCULATION:
  - dayOfMonth field: specific day of month (e.g., 15th)
  - dueDateFormula: "+7days", "+1month", "+90days", "+1quarter", "+1year"
  - Handles leap year edge cases: Math.min(dayOfMonth, maxDay)
  Evidence: resolveSpecificDayOfMonth() lines 199-221
RACI APPROVER RESOLUTION:
  Reads Configuration.policyConfig JSONB → raciRoles.accountable array
  Resolves user names from UserRepository
  Evidence: lines 141-172
FAILURE HANDLING: Per-task try/catch, logs error, continues

### 4.4 TaskOverdueScheduler
FILE: scheduler/TaskOverdueScheduler.java
CRON: @Scheduled(cron = "${task.overdue.cron:0 0 0 * * ?}") — midnight daily
PURPOSE: Mark overdue task instances and send notifications
FLOW:
  1. Query TaskInstances: status NOT IN (COMPLETED, CANCELLED) AND dueDate < today
  2. If not already OVERDUE, update status to OVERDUE
  3. Create in-app notification for assigned user
DEDUPLICATION: Checks wasAlreadyOverdue before updating (line 52-54)
NOTIFICATION: Creates AppNotification of type TASK_OVERDUE

### 4.5 TaskStatusUpdateScheduler
FILE: scheduler/TaskStatusUpdateScheduler.java
CRON: @Scheduled(cron = "${task.status.update.cron:0 0 * * * ?}") — every hour
PURPOSE: Auto-calculate status from action item completion
FLOW:
  1. Query TaskInstances with status IN (PENDING, IN_PROGRESS)
  2. Parse actionItemsJson (JSONB stored as TEXT)
  3. Calculate: 0 completed=PENDING, partial=IN_PROGRESS, all=APPROVAL_PENDING
  4. If status changes, persist and optionally send APPROVAL_PENDING notification
NOTIFICATION DEDUP:
  Uses TaskInstanceNotification table to prevent duplicate APPROVAL_PENDING emails
  Evidence: lines 140-143: notificationRepository.existsByInstanceIdAndEvent()

### 4.6 TaskReminderScheduler
FILE: scheduler/TaskReminderScheduler.java
CRON: Morning = "0 0 9 * * ?", Evening = "0 0 17 * * ?"
PURPOSE: Send task due date reminders twice daily
FLOW:
  1. Find distinct tenant IDs with reminder candidates
  2. For each tenant, delegate to TaskReminderProcessingService
  3. Track totalSent, tenantsProcessed, tenantsFailed
MULTI-TENANT: Processes each tenant independently with failure isolation

### 4.7 TaskGenerationScheduler
FILE: scheduler/TaskGenerationScheduler.java
CRON: @Scheduled(cron = "${task.schedule.cron:0 0 1 * * ?}") — 1 AM daily
PURPOSE: Generate tasks from ComplianceSchedule definitions
FLOW:
  1. Query enabled ComplianceSchedules that are due (nextRunDate <= now)
  2. For each: create Task with default 7-day due date
  3. Update schedule's next run time

### 4.8 RuleEngineMaterializationScheduler (DISABLED)
FILE: scheduler/RuleEngineMaterializationScheduler.java (1102 lines, 48KB)
CRON: @Scheduled(every = "5m") — COMMENTED OUT (line 157)
PURPOSE: Evaluate task applicability against entity profiles using rule engine
THIS IS THE MOST COMPLEX SCHEDULER. Deep dive:

FLOW:
  1. Check if AI mode is enabled (llm_auto_acts_sync.enabled) — skip if true
  2. Get ALL tasks for tenant
  3. For each entity in tenant:
     a. Recompute entity profile from questionnaire responses
     b. Load computed profile fields (typed: boolean, numeric, text)
     c. For each task: extract applicability_conditions from obligation_data_json
     d. Evaluate conditions using local rule engine (NOT AI)
     e. Track applicable acts, compliance status, department counts
  4. Determine winning department per act (highest count wins)
  5. Create task_entity_department_mapping records (ENABLED/DISABLED)
  6. Track progress via ApplicabilityEvaluation entity

CONDITION EVALUATION ENGINE (lines 923-1067):
  - Supports operators: ==, !=, IN, NOT_IN, >, >=, <, <=
  - Supports AND/OR logic between conditions
  - FREE TEXT MATCHING: Uses WordNet synonyms via WordNetService
    semanticMatch() checks if 60%+ of expected tokens match actual tokens
    or their synonyms. Evidence: line 1066: matched/expectedTokens.length >= 0.6
  - NUMERIC COMPARISON: BigDecimal-based for precision
  - Source type awareness: "option" fields use exact match, "free_text" uses semantic

CONCURRENCY GUARD: AtomicBoolean running = new AtomicBoolean(false)
  Evidence: line 84, used in compareAndSet at line 159

### 4.9 LogCleanupScheduler
FILE: scheduler/LogCleanupScheduler.java
CRON: @Scheduled(every = "1h")
PURPOSE: Delete application_logs older than 24 hours
IMPLEMENTATION: Direct JDBC (not Panache) — DELETE FROM application_logs WHERE logged_at < ?
RISK: Uses raw DataSource connection, bypasses Hibernate session

================================================================================
## 5. SECURITY ANALYSIS (DEEP DIVE)
================================================================================

### 5.1 Authentication Flow
1. User logs in via compliance-auth → receives JWT in HttpOnly cookie "access_token"
2. CookieAuthRequestFilter (@PreMatching, AUTHENTICATION priority):
   - Extracts "access_token" cookie from request
   - Validates JWT using JwtService (RSA public key verification)
   - Populates AuthenticatedUser CDI bean with claims
   - Injects Authorization header: "Bearer {token}"
   Evidence: CookieAuthRequestFilter.java lines 38-72
3. PermissionFilter (@AUTHORIZATION priority):
   - Checks if path is PUBLIC (bypasses auth check)
   - Calls securityUtils.checkPermission(path, method)
   - Returns 403 FORBIDDEN or 401 UNAUTHORIZED
   Evidence: PermissionFilter.java lines 51-89

### 5.2 Authorization Model
RBAC: Role-based access control via hardcoded path permission matrix
ROLES (5 levels):
  SUPER_ADMIN — /v1/core/admin/** (exclusive)
  ADMIN — /v1/core/** + /v1/evidence/** (all methods, excludes admin)
  DEPARTMENT_ADMIN — Same as ADMIN (same paths, all methods)
  USER — Granular: dashboard(GET), workspace tasks(GET,PUT), notifications, data-sources(GET)
  VIEWER — Read-only: /v1/core/**(GET), /v1/evidence/**(GET)
  Evidence: RolePermissionConfig.java lines 15-73

PUBLIC PATHS (no auth required):
  - v1/auth/login, v1/auth/logout, v1/auth/register, v1/auth/refresh
  - v1/core/public/*, v1/core/internal/* (service-to-service)
  - q/health, q/metrics, q/openapi
  Evidence: PermissionFilter.java lines 26-41

CRITICAL GAP: Internal endpoints (/v1/core/internal/*) are PUBLIC
  This means any network-reachable client can call materialization and profile endpoints
  without authentication. In production, these should be network-isolated.

### 5.3 JWT Structure
Claims extracted: sub (userId), email, entityId, tenantId, firstName, lastName, groups
Token signed with RSA private key (compliance-auth), verified with public key (all services)
Token expiry: 3600s (1 hour) for access, 604800s (7 days) for refresh
Evidence: application-dev.properties lines 22-24

================================================================================
## 6. INTEGRATION ANALYSIS (DEEP DIVE)
================================================================================

### 6.1 MDM Integration (SubscriptionClient, MdmActClient)
TYPE: Synchronous REST (MicroProfile REST Client)
PATTERN: Dynamic URL resolution per tenant via MdmClientFactory
AUTHENTICATION: OAuth2 client_credentials flow
  Evidence: MdmTokenService.java — getToken("client_credentials", clientId, clientSecret, scope)
TOKEN CACHING: ConcurrentHashMap with 300-second expiry buffer
  Evidence: MdmTokenService.java lines 31-32, line 117
ENDPOINTS CALLED:
  - GET /api/subscription/acts — List available acts
  - POST /api/subscription/subscriptions — Subscribe to acts
  - GET /api/subscription/jobs — List snapshot jobs
  - GET /api/subscription/jobs/{jobId}/chunks/{chunkNumber} — Get snapshot chunk
  - POST /api/subscription/jobs/{jobId}/consume — Mark job consumed
  - POST /api/subscription/jobs/trigger — Trigger snapshot generation
  - PUT /api/subscription/subscriptions/status — Sync subscription status
  Evidence: SubscriptionClient.java lines 28-84

### 6.2 Compliance AI Integration (ComplianceAiClient)
TYPE: MicroProfile REST Client (async Uni + sync)
BASE URL: configKey "compliance-ai-client"
ENDPOINTS CALLED:
  - POST /api/v1/core/internal/ai/document/process — AI document processing (async/Uni)
  - POST /api/v1/core/internal/ai/gap-analysis — Submit gap analysis (returns jobId)
  - GET /api/v1/core/internal/ai/gap-analysis/{jobId}/result — Poll gap analysis result
  - POST /api/v1/core/internal/ai/applicability/evaluate — Task applicability (sync)
  Evidence: ComplianceAiClient.java lines 32-87

### 6.3 Keka HR Integration (KekaSyncService)
TYPE: Direct HTTP client (java.net.http.HttpClient), NOT MicroProfile REST Client
AUTHENTICATION: OAuth2 with grant_type=kekaapi (Keka-specific)
  Evidence: KekaSyncService.java line 62: "grant_type=kekaapi"
BASE URL: https://{subdomain}.keka.com/api/v1/
EVIDENCE CATEGORIES (12):
  EPF, ESI, MINIMUM_WAGES, WORKING_HOURS, LEAVE_REGISTER, HOLIDAY_CALENDAR,
  MATERNITY_LEAVE, EQUAL_REMUNERATION, CONTRACT_LABOUR, APPRENTICESHIP,
  FORM_16, GRATUITY
API ENDPOINTS USED:
  - /payroll/runs — PF and ESI contribution data
  - /payroll/employees — Salary data for minimum wages
  - /payroll/employees/{id}/salarycomponents — Tax components for Form 16
  - /attendance/timesheets — Working hours data
  - /time/leaverequests — Leave register + maternity leave
  - /time/holidays — Holiday calendar
  - /hris/employees — Employee data for equal remuneration, contract labour, gratuity
  - /hris/departments — Connection test probe
  Evidence: KekaSyncService.java lines 117-399

### 6.4 MdmClientFactory (Dynamic REST Client)
PATTERN: Factory pattern for building REST clients dynamically
  Uses RestClientBuilder.newBuilder() instead of @Inject @RestClient
  Resolves MDM base URL from MdmTenant.mdmBaseUrl (per-tenant configuration)
  Appends service path: /mdm-core for OAuth, /mdm-subscriptions for subscription
  Evidence: MdmClientFactory.java lines 30-104
WHY: Each tenant may connect to a different MDM deployment (multi-MDM support)
TIMEOUT: connectTimeout=5s, readTimeout=30s

================================================================================
## 7. ENTITY ANALYSIS (CRITICAL ENTITIES)
================================================================================

### Task Entity
TABLE: tasks
FIELDS:
  id (UUID), name, description, status (TO_DO/IN_PROGRESS/APPROVAL_PENDING/COMPLETED/OVERDUE),
  severity (CRITICAL/HIGH/MEDIUM/LOW), penalty (BigDecimal), progress (Integer),
  startDate, dueDate, assignedUsers (JSONB), actName, ruleName,
  recurrenceType (ONE_TIME/MONTHLY/QUARTERLY/HALF_YEARLY/YEARLY),
  nextOccurrenceDate, occurrenceCount, dueDateFormula, isEnabled, isActive,
  dayOfMonth, applicabilityConditions (JSONB), obligationDataJson (JSONB),
  externalObligationId, obligationVersion, obligationEffectiveFrom, obligationStatus,
  instanceStatus (PENDING_ASSIGNMENT/PENDING_INFO/READY/INSTANCES_CREATED/NEEDS_REGENERATION)
RELATIONSHIPS:
  ManyToOne → Compliance (compliance_id)
  ManyToOne → User (assigned_user_id) — lazy
  ManyToOne → Department (department_id) — lazy
  ManyToOne → BusinessEntity (entity_id) — lazy
  ManyToOne → Tenant (tenant_id) — lazy
  OneToMany → TaskActionItem (mappedBy="task", CASCADE ALL)
INDEXES:
  idx_tasks_compliance_id, idx_tasks_assigned_user_id, idx_tasks_status, idx_tasks_entity_id
DESIGN NOTES:
  - assignedUsers is JSONB: {"entityId": {"userId": "...", "userName": "..."}}
    Allows one task template to have different assignees per business entity
  - obligationDataJson stores raw MDM data at subscription time
    Reason: "instance generation runs later in compliance-ai (no live MDM call)"
  Evidence: Task.java lines 146-152

### TaskInstance Entity
TABLE: task_instances
FIELDS:
  id, templateId (→ task.id), taskId, instanceTitle, dueDate, status (PENDING/IN_PROGRESS/
  APPROVAL_PENDING/COMPLETED/OVERDUE/CANCELLED), priority, assignedTo (userId),
  approverIds (JSONB list), approverNames (JSONB list), companyId (entityId),
  actionItemsJson (TEXT), completedAt, lastNotifiedAt, tenantId, progress, occurrenceNumber
DESIGN: No FK to tasks — uses string taskId for loose coupling
  This allows instances to survive task template deletion

### BusinessEntity Entity
TABLE: entities
FIELDS:
  id, name, description, type (COMPANY/FIRM), industryType, country, city, stateProvince,
  pincode, totalEmployees, pfEligibleCount, esicEligibleCount, pfApplicable, pfRegistrationNumber,
  esicApplicable, esicRegistrationNumber, annualIncome, financialYearEnd,
  profileData (JSONB), isActive, subscriptionId, subscriptionStatus, subscribedAt, expiresAt
RELATIONSHIP: ManyToOne → Tenant
INDEXES: idx_entities_tenant_id, idx_entities_name
DESIGN: Indian-specific compliance fields (PF, ESIC) baked into entity model

### Tenant Entity
TABLE: tenants
FIELDS: id, name, slug (unique), description, isActive, isOnboarded
UNIQUENESS: name (unique), slug (unique)

### Compliance Entity
TABLE: compliances
DESIGN: Represents a compliance rule/regulation under an Act

### Act Entity
TABLE: acts
DESIGN: Represents a legal act/legislation (hierarchical: Act → Compliance → Task)

================================================================================
## 8. CONFIGURATION ANALYSIS
================================================================================

FILE: application-dev.properties
KEY CONFIGURATIONS:
  quarkus.http.port=8080
  quarkus.datasource.jdbc.url=jdbc:postgresql://nyai-metadata-db-dev.postgres.database.azure.com:5432/compliance_dev
  quarkus.datasource.jdbc.min-size=5, max-size=20
  quarkus.hibernate-orm.database.generation=none (schema managed externally)
  quarkus.transaction-manager.default-transaction-timeout=1800 (30 minutes!)
  mp.jwt.verify.publickey.location=keys/publicKey.pem
  jwt.access-token-expiry-seconds=3600
  jwt.refresh-token-expiry-seconds=604800
  falkordb.host=localhost, falkordb.port=6379
  quarkus.http.cors.origins=http://localhost:3000,http://127.0.0.1:3000
  quarkus.tls.trust-all=true (DEV ONLY — security risk in prod)
  oauth.service.url=https://mdm.dev.nyai.ai/mdm-core
  subscription.service.url=https://mdm.dev.nyai.ai/mdm-subscriptions

CONFIGURABLE SCHEDULER CRONS:
  task.recurrence.cron = 0 0 1 * * ? (1 AM daily)
  task.overdue.cron = 0 0 0 * * ? (midnight daily)
  task.status.update.cron = 0 0 * * * ? (every hour)
  task.reminder.cron.morning = 0 0 9 * * ? (9 AM)
  task.reminder.cron.evening = 0 0 17 * * ? (5 PM)
  task.schedule.cron = 0 0 1 * * ? (1 AM daily)

FEATURE FLAGS:
  task.recurrence.enabled = true
  task.overdue.enabled = true
  task.status.update.enabled = true
  task.reminder.enabled = true
  task.schedule.enabled = true

================================================================================
## 9. AUDIT TRAIL SYSTEM (DEEP DIVE)
================================================================================

PATTERN: CDI Transactional Observer
FILE: audit/EntityAuditObserver.java

HOW IT WORKS:
  1. Business service fires CDI event: Event<EntityAuditEvent>.fire()
  2. EntityAuditObserver.onEntityAuditEvent() is called AFTER_SUCCESS
     @Observes(during = TransactionPhase.AFTER_SUCCESS)
  3. Observer runs in REQUIRES_NEW transaction
  4. Creates AuditLog entity with resolved FK references

WHY AFTER_SUCCESS:
  - Ensures audited entity is committed and visible (FK constraints satisfied)
  - Audit failure never rolls back business operation
  Evidence: EntityAuditObserver.java line 36-37

AUDIT LOG FIELDS:
  action, entityType, recordEntityId, details, performedBy
  FK: task, compliance, entity (BusinessEntity), tenant

INTERVIEW QUESTION: "Why not use database triggers for audit?"
ANSWER: Application-level audit captures business context (who, why) that
  triggers cannot access. Also avoids database coupling and works across
  multiple database types.

================================================================================
END OF COMPLIANCE-CORE ANALYSIS
================================================================================
