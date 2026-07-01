================================================================================
07_MDM-INITIAL-DATA FORENSIC ANALYSIS
SERVICE: mdm-initial-data
DATABASE: mdm_dev (PostgreSQL)
FRAMEWORK: Quarkus 3.30.6 + Liquibase
================================================================================

================================================================================
## 1. SERVICE OVERVIEW
================================================================================

PURPOSE:
A dedicated database migration and seeding service for the shared Master Data
Management database (`mdm_dev`). It runs Liquibase changelogs to establish schemas,
seed data, and execute versioned database upgrades before the MDM services boot.

WHY THIS SERVICE EXISTS:
Similar to `compliance-initial-data`, the MDM ecosystem has multiple services
(`mdm-core` and `mdm-subscriptions`) that interact with the same database. To
prevent schema creation race conditions from Hibernate, this dedicated container
manages the DDL using Liquibase migrations.

================================================================================
## 2. LIQUIBASE STRUCTURE ANALYSIS
================================================================================

Evidence: src/main/resources/db/changelog/db.changelog-master.xml

### Baseline v4.0.0
The baseline schema covers the entire `mdm_dev` domain:
- 003-core-users-tenants.xml (users, tenants, oauth_clients, oauth_keys, oauth_access_tokens) -> Auth & Tenant management.
- 004-legal-documents.xml (legal_documents, provisions, provision_versions)
- 005-obligations.xml (obligations, cross_references)
- 006-packages.xml (tenant_act_assignments)
- 007-ingestion.xml (change_log, raw_documents) -> Used for delta tracking.
- 008-subscriptions.xml (subscriptions, subscription_cursors, snapshot_jobs, change_jobs) -> Consumed by `mdm-subscriptions`.
- 009-views.xml (Materialized views for querying).

### Incremental Migrations (v4.0.1+)
- 014-entity-subscriptions.xml: Tracking billing and sub-tenant state for acts.

================================================================================
## 3. INTERVIEW DISCUSSION POINTS (SYSTEM DESIGN)
================================================================================

Q: Why separate the database migration into its own deployment artifact?
A: In an Enterprise architecture with multiple microservices sharing databases (like
   `mdm-core` and `mdm-subscriptions` sharing `mdm_dev`), letting the application
   services run migrations on startup is dangerous. It leads to lock contention,
   split-brain scenarios during rolling deployments, and makes rollback difficult.
   By isolating Liquibase into `mdm-initial-data`, the CI/CD pipeline deploys this
   first. Once the DB schema is verified as upgraded, the stateless application
   services are rolled out. This guarantees schema stability.

================================================================================
END OF MDM-INITIAL-DATA ANALYSIS
================================================================================
