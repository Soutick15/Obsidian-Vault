================================================================================
06_COMPLIANCE-INITIAL-DATA FORENSIC ANALYSIS
SERVICE: compliance-initial-data
DATABASE: compliance_dev (PostgreSQL)
FRAMEWORK: Quarkus 3.30.6 + Liquibase
================================================================================

================================================================================
## 1. SERVICE OVERVIEW
================================================================================

PURPOSE:
A dedicated database migration and seeding service for the shared compliance database
(`compliance_dev`). It runs Liquibase changelogs to establish schemas, seed data,
and execute versioned database upgrades before the core services boot.

WHY THIS SERVICE EXISTS:
Because `compliance-core`, `compliance-auth`, and `compliance-ai` all share the
same database, allowing Hibernate to auto-generate the schema from any one of
these services would create race conditions and schema corruption. By centralizing
Database Definition Language (DDL) into a single, idempotent migration service,
we guarantee database consistency.

All consumer services (`compliance-core`, `compliance-auth`, `compliance-ai`)
have `quarkus.hibernate-orm.database.generation=none` configured.

================================================================================
## 2. LIQUIBASE STRUCTURE ANALYSIS
================================================================================

Evidence: src/main/resources/db/changelog/db.changelog-master.xml

### Baseline v4.0.0
The baseline schema covers the entire `compliance_dev` domain:
- 001-extensions.xml (uuid-ossp, pgcrypto, etc.)
- 002-core-tenants.xml (tenants, entities, departments, tenant_settings)
- 003-auth-users.xml (roles, users, refresh_tokens) -> Used by `compliance-auth`
- 004-legal-acts.xml -> Used by `compliance-core`
- 005-compliances.xml
- 006-tasks.xml
- 007-data-sources.xml
- 008-evidence.xml (ai_evidence_suggestions) -> Used by `compliance-ai`
- 009-notifications.xml
- 010-operations.xml
- 011-mdm-integration.xml -> Subscription sync tables used to talk to `mdm-subscriptions`
- 012-indexes.xml

### Incremental Migrations (v4.0.1+)
- 014/015: Massive questionnaire schema and seed data (24 sections, 125 questions, 1531 options).
- 062: Acts entity mapping refactoring.
- 063: MDM sync state for Excel imports.
- 065: Gap discovery locks.

================================================================================
## 3. INTERVIEW DISCUSSION POINTS (SYSTEM DESIGN)
================================================================================

Q: How do you manage schema migrations in a multi-service architecture sharing a database?
A: We use a dedicated Migration Service pattern (`compliance-initial-data`). The ORM
   auto-generation (Hibernate `update` or `create-drop`) is strictly disabled across
   all consumer microservices. Instead, a CI/CD pipeline deploys this migration
   service first. It uses Liquibase to run idempotent XML changelogs, establish locks,
   and upgrade the schema. Only after it succeeds do the other services boot.

Q: Why not use Flyway inside `compliance-core`?
A: If both `compliance-core` and `compliance-auth` restart simultaneously and both
   run Flyway/Liquibase, they will race to acquire the database lock. While Flyway
   handles locks, isolating migrations to a separate container guarantees proper
   separation of concerns and zero-downtime deployment orchestration (Migrate ->
   Deploy new code -> Deprecate old code).

================================================================================
END OF COMPLIANCE-INITIAL-DATA ANALYSIS
================================================================================
