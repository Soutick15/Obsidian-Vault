================================================================================
00_REPOSITORY_INVENTORY.txt
ComplianceManagementSystem Platform — Full Repository Forensic Inventory
Generated from source code analysis — NOT assumptions
================================================================================

## 1. REPOSITORY STRUCTURE

Root: /ComplianceManagementSystem/
├── compliance-core/           # Main tenant-facing compliance engine (port 8080)
├── compliance-auth/           # Authentication & authorization service (port 8085)
├── compliance-ai/             # AI/LLM intelligence engine (port 8086)
├── compliance-initial-data/   # Schema migration runner for compliance DB
├── mdm-core/                  # Master Data Management — global legal data repository
├── mdm-subscriptions/         # MDM tenant subscription & snapshot delivery
├── mdm-initial-data/          # Schema migration runner for MDM DB
├── ComplianceManagementSystem_Architecture_Overview.txt
└── MDM_SUBSCRIPTION_CONTEXT.md

Total Services: 7 (5 runtime + 2 schema-only)

================================================================================
## 2. MICROSERVICE INVENTORY
================================================================================

┌─────────────────────────┬──────────┬───────────────┬─────────────────────────────────────┐
│ Service                 │ Port     │ Framework     │ Primary Database                    │
├─────────────────────────┼──────────┼───────────────┼─────────────────────────────────────┤
│ compliance-core         │ 8080     │ Quarkus 3.30.6│ compliance_dev (Azure PostgreSQL)   │
│ compliance-auth         │ 8085     │ Quarkus 3.30.6│ compliance_dev (SHARED with core)   │
│ compliance-ai           │ 8086     │ Quarkus 3.30.6│ compliance_dev (SHARED with core)   │
│ compliance-initial-data │ N/A      │ Quarkus 3.30.6│ compliance_dev (migration runner)   │
│ mdm-core                │ 9090     │ Quarkus 3.30.6│ mdm_dev (Azure PostgreSQL)          │
│ mdm-subscriptions       │ 9091     │ Quarkus 3.30.6│ mdm_dev (SHARED with mdm-core)      │
│ mdm-initial-data        │ N/A      │ Quarkus 3.30.6│ mdm_dev (migration runner)          │
└─────────────────────────┴──────────┴───────────────┴─────────────────────────────────────┘

Evidence:
  - compliance-core port: application-dev.properties line 6: quarkus.http.port=8080
  - compliance-auth port: application-dev.properties line 6: quarkus.http.port=8085
  - compliance-ai port: application-dev.properties line 6: quarkus.http.port=8086
  - All services: pom.xml → quarkus.platform.version = 3.30.6
  - Database URL: jdbc:postgresql://ComplianceManagementSystem-metadata-db-dev.postgres.database.azure.com:5432/compliance_dev

================================================================================
## 3. FRAMEWORK & TECHNOLOGY STACK
================================================================================

### Core Runtime
- Java 21 (maven.compiler.release=21 in all pom.xml)
- Quarkus 3.30.6 (quarkus-bom)
- GraalVM Mandrel builder image for native compilation
  Evidence: Dockerfile line 2: FROM maven:3.9-eclipse-temurin-21
  Evidence: application-dev.properties: quarkus.native.builder-image=quay.io/quarkus/ubi-quarkus-mandrel-builder-image:jdk-21

### Persistence
- PostgreSQL 18 (Azure-hosted: ComplianceManagementSystem-metadata-db-dev.postgres.database.azure.com)
- Hibernate ORM with Panache (quarkus-hibernate-orm-panache)
- Flyway (quarkus-flyway) — disabled in core services, run by *-initial-data
- JSONB columns heavily used (SqlTypes.JSON, JdbcTypeCode)

### Graph Database
- FalkorDB via Jedis 5.1.0 (redis.clients:jedis)
  Evidence: compliance-core application-dev.properties: falkordb.host=localhost, falkordb.port=6379
  Evidence: compliance-ai pom.xml: redis.clients:jedis:5.1.0

### Security
- SmallRye JWT (quarkus-smallrye-jwt)
- BCrypt (org.mindrot:jbcrypt:0.4)
- BouncyCastle for PEM key parsing (bcpkix-jdk18on:1.78.1)
- RSA Asymmetric JWT: privateKey.pem (auth only) + publicKey.pem (all services)
  Evidence: compliance-core application-dev.properties line 17-19:
    mp.jwt.verify.publickey.location=keys/publicKey.pem
    smallrye.jwt.sign.key.location=keys/privateKey.pem

### Document Processing
- Apache Tika 2.9.2 (tika-core + tika-parsers-standard-package)
  Evidence: compliance-ai pom.xml lines 75-91

### NLP / Semantic Matching
- extJWNL (WordNet) — used in compliance-core for semantic condition matching
  Evidence: RuleEngineMaterializationScheduler.java line 46: WordNetService import
  Evidence: semanticMatch() method line 1054-1067: uses wordNetService.getSynonyms()

### AI / LLM
- Anthropic Claude API via custom AiClientHelper
  Evidence: compliance-ai ClaudeRankingService.java: SYSTEM_PROMPT for compliance ranking
  Evidence: AiClientHelper.java: custom REST client wrapper

### Email
- Eclipse Angus Mail (jakarta.mail)
  Evidence: compliance-core pom.xml: org.eclipse.angus:angus-mail

### Observability
- Micrometer + Prometheus (quarkus-micrometer-registry-prometheus)
- SmallRye Health (quarkus-smallrye-health)
- SmallRye OpenAPI + Swagger UI

### Code Generation
- Lombok 1.18.30

================================================================================
## 4. INFRASTRUCTURE DEPENDENCIES
================================================================================

1. Azure PostgreSQL (ComplianceManagementSystem-metadata-db-dev.postgres.database.azure.com)
   - Database: compliance_dev (shared by compliance-core, compliance-auth, compliance-ai)
   - Database: mdm_dev (shared by mdm-core, mdm-subscriptions)

2. FalkorDB (Redis-compatible graph database)
   - Host: localhost:6379 (dev), compliance_graph
   - Used for: compliance relationship traversal via Cypher queries

3. Anthropic Claude API
   - Accessed via AiClientHelper in compliance-ai
   - Used for: evidence ranking, gap analysis, applicability evaluation

4. MDM Portal (external)
   - URL: https://mdm.dev.ComplianceManagementSystem.ai/mdm-core (OAuth service)
   - URL: https://mdm.dev.ComplianceManagementSystem.ai/mdm-subscriptions (subscription service)
   Evidence: compliance-core application-dev.properties lines 64-69

================================================================================
## 5. DEPLOYMENT ARTIFACTS
================================================================================

### Docker Setup
- Multi-stage Dockerfile per service
  Stage 1: maven:3.9-eclipse-temurin-21 (build)
  Stage 2: registry.access.redhat.com/ubi9/openjdk-21-runtime:1.21 (runtime)
- Profile: QUARKUS_PROFILE=k8s for production
- Runs as non-root user (UID 185)
  Evidence: Dockerfile line 21: USER 185

### Container Base Image
- Red Hat UBI9 OpenJDK 21 Runtime
- Production-grade, RHEL-based, hardened image

================================================================================
## 6. MONITORING SETUP
================================================================================

- Health endpoints: /q/health, /q/health/live, /q/health/ready
- Metrics endpoint: /q/metrics (Prometheus format)
- Swagger UI: /q/swagger-ui
- OpenAPI spec: /q/openapi
  Evidence: compliance-core application-dev.properties lines 41-47
  Evidence: compliance-ai application-dev.properties lines 58-71

================================================================================
## 7. SERVICE DEPENDENCY DIAGRAM (Text)
================================================================================

                    ┌──────────────────┐
                    │   Frontend App   │
                    │ (React/Angular)  │
                    │ localhost:3000   │
                    └────────┬─────────┘
                             │ REST + HttpOnly Cookie
                    ┌────────▼─────────┐
                    │ compliance-auth  │───── Signs JWT (Private Key)
                    │     :8085        │───── BCrypt password hashing
                    └────────┬─────────┘
                             │ JWT in HttpOnly Cookie
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼─────┐ ┌─────▼──────┐ ┌─────▼──────────┐
     │compliance-core│ │compliance-ai│ │ (Future svc)   │
     │    :8080      │ │   :8086    │ │                │
     │ Verifies JWT  │ │Verifies JWT│ │ Verifies JWT   │
     │ (Public Key)  │ │(Public Key)│ │ (Public Key)   │
     └───────┬───────┘ └─────┬──────┘ └────────────────┘
             │               │
             │  REST Client  │
             ├───────────────┤
             │               │
     ┌───────▼───────┐ ┌────▼──────────┐
     │ FalkorDB      │ │ Claude API    │
     │ (Graph DB)    │ │ (Anthropic)   │
     │ :6379         │ │               │
     └───────────────┘ └───────────────┘
             │
             │  REST Client (SubscriptionClient)
             │
     ┌───────▼───────────────┐
     │  mdm-subscriptions    │───┐ SHARED DATABASE
     │       :9091           │   │ (mdm_dev)
     └───────────────────────┘   │
							   |│
     ┌───────────────────────┐   │
     │     mdm-core          │───┘
     │       :9090           │
     └───────────────────────┘

     ┌───────────────────────┐     ┌───────────────────────┐
     │compliance-initial-data│     │  mdm-initial-data     │
     │  (Schema Migrator)    │     │  (Schema Migrator)    │
     │  Flyway → compliance  │     │  Liquibase → mdm_dev  │
     └───────────────────────┘     └───────────────────────┘

================================================================================
## 8. DOMAIN BOUNDARIES
================================================================================

DOMAIN 1: COMPLIANCE (Tenant-Facing)
  Bounded Context: Tenant task management, evidence tracking, compliance monitoring
  Services: compliance-core, compliance-auth, compliance-ai, compliance-initial-data
  Database: compliance_dev
  Domain Entities: Tenant, BusinessEntity, Department, User, Task, TaskInstance,
                   Compliance, Act, Obligation, Configuration, DataSource, etc.

DOMAIN 2: MASTER DATA MANAGEMENT (Global, Platform-Wide)
  Bounded Context: Global legal data repository, act/provision management
  Services: mdm-core, mdm-subscriptions, mdm-initial-data
  Database: mdm_dev
  Domain Entities: LegalDocument, Provision, Obligation, ProvisionVersion,
                   Subscription, SnapshotJob, etc.

CROSS-DOMAIN COMMUNICATION:
  - compliance-core → mdm-subscriptions (REST Client: SubscriptionClient)
  - compliance-core → mdm-core (REST Client: MdmActClient, OAuthClient)
  - Communication: Pull-based polling via SubscriptionSyncScheduler
  - Data sync: Sequence number tracking (NOT event-driven)
  Evidence: SubscriptionSyncScheduler.java: @Scheduled(every = "10m")
  Evidence: SubscriptionClient.java: REST endpoints for /api/subscription/*

================================================================================
## 9. BOUNDED CONTEXT MAP
================================================================================

┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE DOMAIN                                │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ compliance-  │  │ compliance-  │  │ compliance-  │              │
│  │    core      │  │    auth      │  │     ai       │              │
│  │              │  │              │  │              │              │
│  │ Tasks        │  │ Users        │  │ Evidence     │              │
│  │ Instances    │  │ Roles        │  │ Ranking      │              │
│  │ Departments  │  │ JWT          │  │ Gap Analysis │              │
│  │ Entities     │  │ Permissions  │  │ Questionnaire│              │
│  │ Compliance   │  │ Sessions     │  │ Applicability│              │
│  │ Subscriptions│  │              │  │ FalkorDB     │              │
│  │ Scheduling   │  │              │  │ Claude AI    │              │
│  └──────┬───────┘  └──────────────┘  └──────────────┘              │
│         │                                                           │
│         │ SHARED DATABASE: compliance_dev (Azure PostgreSQL)        │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          │  Customer-Supplier (Pull Polling)
          │  REST Client + Sequence Numbers
          │
┌─────────▼───────────────────────────────────────────────────────────┐
│                    MDM DOMAIN                                       │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │   mdm-core   │  │    mdm-      │                                │
│  │              │  │ subscriptions│                                │
│  │ Legal Docs   │  │ Snapshots    │                                │
│  │ Provisions   │  │ Chunked Jobs │                                │
│  │ Obligations  │  │ Act Delivery │                                │
│  │ Versions     │  │ Tenant Subs  │                                │
│  └──────────────┘  └──────────────┘                                │
│                                                                     │
│         SHARED DATABASE: mdm_dev (Azure PostgreSQL)                 │
└─────────────────────────────────────────────────────────────────────┘

================================================================================
## 10. RESPONSIBILITY MATRIX
================================================================================

┌─────────────────────┬─────────────────────────────────────────────────────┐
│ Responsibility      │ Service                                             │
├─────────────────────┼─────────────────────────────────────────────────────┤
│ User Authentication │ compliance-auth (JWT signing, BCrypt, login/logout) │
│ User Authorization  │ compliance-core (PermissionFilter, RolePermConfig)  │
│ Task CRUD           │ compliance-core (TaskResource, TaskService)         │
│ Task Recurrence     │ compliance-core (TaskRecurrenceScheduler)           │
│ Task Overdue Check  │ compliance-core (TaskOverdueScheduler)              │
│ Task Reminders      │ compliance-core (TaskReminderScheduler)             │
│ Task Status Auto    │ compliance-core (TaskStatusUpdateScheduler)         │
│ Rule Engine         │ compliance-core (RuleEngineMaterializationScheduler)│
│ MDM Data Sync       │ compliance-core (SubscriptionSyncScheduler)         │
│ Dashboard Analytics │ compliance-core (DashboardResource)                 │
│ Entity Management   │ compliance-core (EntityResource)                    │
│ Department Mgmt     │ compliance-core (DepartmentResource)                │
│ Evidence Ranking    │ compliance-ai (ClaudeRankingService)                │
│ Gap Analysis        │ compliance-ai (GapAnalysisService)                  │
│ Doc Processing      │ compliance-ai (AiSourceDocumentProcessor)           │
│ Questionnaire AI    │ compliance-ai (QuestionnaireAiResolutionService)    │
│ Graph Sync          │ compliance-ai (MaterializationSyncRunner)           │
│ Legal Data Store    │ mdm-core                                            │
│ Snapshot Generation │ mdm-subscriptions                                   │
│ Schema Migration    │ compliance-initial-data, mdm-initial-data           │
│ Audit Trail         │ compliance-core (EntityAuditObserver)               │
│ Email Notifications │ compliance-core (NotificationService, Eclipse Mail) │
│ In-App Notifications│ compliance-core (AppNotificationService)            │
│ Keka HR Integration │ compliance-core (KekaSyncService)                   │
└─────────────────────┴─────────────────────────────────────────────────────┘

================================================================================
## 11. CRITICAL ARCHITECTURAL DECISIONS (PROVEN BY CODE)
================================================================================

1. SHARED DATABASE PATTERN (anti-pattern, intentional)
   - compliance-core + compliance-auth + compliance-ai → compliance_dev
   - mdm-core + mdm-subscriptions → mdm_dev
   Evidence: All services point to same JDBC URL in application-dev.properties

2. SCHEMA MIGRATION EXTERNALIZED
   - quarkus.flyway.migrate-at-start=false in compliance-auth (line 23)
   - quarkus.hibernate-orm.database.generation=none in compliance-core (line 35)
   - Migrations run by compliance-initial-data / mdm-initial-data

3. PULL-BASED SYNC (No Kafka/RabbitMQ)
   - SubscriptionSyncScheduler runs every 10 minutes
   - Uses sequence_number based delta polling
   Evidence: SubscriptionSyncScheduler.java line 32: @Scheduled(every = "10m")

4. COOKIE-BASED JWT TRANSPORT
   - JWT stored in HttpOnly cookie named "access_token"
   - CookieAuthRequestFilter extracts token from cookie, injects into Authorization header
   Evidence: CookieAuthRequestFilter.java line 28: auth.cookie.name=access_token

5. CUSTOM RBAC (Not @RolesAllowed)
   - RolePermissionConfig: hardcoded path-based permission matrix
   - Roles: SUPER_ADMIN, ADMIN, DEPARTMENT_ADMIN, USER, VIEWER
   - PermissionFilter checks path + HTTP method against role matrix
   Evidence: RolePermissionConfig.java lines 15-73

6. TRANSACTION TIMEOUT 30 MINUTES
   - quarkus.transaction-manager.default-transaction-timeout=1800
   Evidence: application-dev.properties line 105
   Risk: Long-running snapshot processing could hold DB locks

================================================================================
END OF REPOSITORY INVENTORY
================================================================================
