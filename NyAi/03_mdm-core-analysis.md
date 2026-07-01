================================================================================
03_MDM-CORE FORENSIC ANALYSIS
SERVICE: mdm-core
DATABASE: mdm_db (PostgreSQL)
FRAMEWORK: Quarkus 3.30.6
================================================================================

================================================================================
## 1. SERVICE OVERVIEW
================================================================================

PURPOSE:
The Master Data Management (MDM) core service. Acts as the central, authoritative
source of truth for all legal content in the NyAi ecosystem. It manages the legal
hierarchy (Acts → Rules/Regulations → Provisions → Obligations). It also manages
tenant onboarding into the MDM ecosystem and issues OAuth client credentials for
them to pull data.

BUSINESS RESPONSIBILITY:
- Manage Legal Documents (Acts, Rules, Regulations).
- Manage Provisions (sections of acts/rules) and versioning.
- Manage Obligations (actionable items derived from provisions).
- Multi-tenant SaaS management (creating tenants, assigning acts).
- Issue and manage OAuth2 client credentials for tenant systems.
- Track all mutations to legal data using an interceptor (ChangeLog) for delta syncs.
- LLM Analytics integration.

WHY THIS SERVICE EXISTS:
Centralizes the legal research and compliance ruleset into one global database
(`mdm_db`). Instead of every tenant maintaining their own database of laws,
SMEs (Subject Matter Experts) update `mdm-core`. Tenants subscribe to changes
and pull updates to their local `compliance-core` instances.

PROBLEM SOLVED:
Provides a single pane of glass for legal content management and tenant onboarding.
Enables a publish/subscribe model for regulatory updates via a pull-based OAuth2 API.

================================================================================
## 2. PACKAGE ANALYSIS
================================================================================

### Package: com.nyai.mdm.controller
- TenantController.java — Tenant CRUD, Act assignment, OAuth client generation.
- LegalDocumentController.java — Acts, Rules, Regulations CRUD and hierarchy traversal.
- ProvisionsController.java — Provision management.
- ObligationsController.java — Obligation CRUD.
- OAuthController.java — RFC 6749 Token Endpoint (`/token`), Introspect, Revoke.
- AuthController.java — Admin/SME login to MDM dashboard.

### Package: com.nyai.mdm.model & .entity
- LegalDocument.java — Represents an Act, Rule, or Regulation.
- Provision.java — Represents a section/chapter of a document.
- Obligation.java — The actual compliance requirement derived from a provision.
- Tenant.java — MDM representation of a customer.
- OAuthClient.java, OAuthAccessToken.java — MDM acting as an Authorization Server.
- TenantActAssignment.java — Maps which acts a tenant is subscribed to.

### Package: com.nyai.mdm.repository
- LegalDocumentRepository.java — Uses Panache + Native SQL queries.
- ProvisionRepository.java
- ObligationRepository.java
- TenantRepository.java
- OAuthClientRepository.java

### Package: com.nyai.mdm.security
- JwtAuthenticationFilter.java — Validates JWT tokens from requests.
- AuthorizationMiddleware.java — Enforces RBAC permissions based on UserRole.
- JwtTokenProvider.java — Validates self-issued tokens (for SMEs/Admins).

### Package: com.nyai.mdm.interceptor
- ChangeLogInterceptor.java — `@AroundInvoke` interceptor on service methods to track mutations.
- @ChangeLogged — Annotation marker.

================================================================================
## 3. CONTROLLER ANALYSIS — CRITICAL ENDPOINTS
================================================================================

### TenantController.java — /api/v1/admin/tenants
Evidence: controller/TenantController.java

┌──────────────────────────────┬────────┬─────────────────────────────────────┐
│ Endpoint                     │ Method │ Purpose                             │
├──────────────────────────────┼────────┼─────────────────────────────────────┤
│ /                            │ POST   │ Create tenant                       │
│ /{tenantId}/oauth/clients    │ POST   │ Create OAuth client for tenant      │
│ /{tenantId}/acts             │ POST   │ Assign specific Acts to tenant      │
│ /{tenantId}/acts             │ GET    │ Get assigned Acts for tenant        │
│ /{tenantId}/metadata/download│ GET    │ Download tenant connection JSON     │
└──────────────────────────────┴────────┴─────────────────────────────────────┘
SECURITY: ADMIN role only.
KEY LOGIC: When a tenant is created, `TenantServiceImpl` creates an OAuthClient
and generates a plain text secret. This secret is returned ONLY ONCE in the response
or via the metadata download.

### OAuthController.java — /oauth
Evidence: controller/OAuthController.java

┌──────────────┬────────┬─────────────────────────────────────┐
│ Endpoint     │ Method │ Purpose                             │
├──────────────┼────────┼─────────────────────────────────────┤
│ /token       │ POST   │ client_credentials grant flow       │
│ /introspect  │ POST   │ Token introspection (RFC 7662)      │
│ /revoke      │ POST   │ Token revocation (RFC 7009)         │
└──────────────┴────────┴─────────────────────────────────────┘
SECURITY: Public endpoints, expects `Basic Auth` with `client_id:client_secret`.
KEY LOGIC: Validates `client_credentials`, generates a JWT access token representing
the specific tenant client.

### LegalDocumentController.java — /api/v1/acts
- Provides hierarchical endpoints:
  - GET `/api/v1/acts/{actId}/rules`
  - GET `/api/v1/acts/{actId}/regulations`
KEY LOGIC: Traverses the `parent_document_id` hierarchy. Regulations can be direct
children of acts, or grandchildren (children of rules).

================================================================================
## 4. SERVICE ANALYSIS (DEEP DIVE)
================================================================================

### TenantServiceImpl.java
Evidence: serviceimpl/TenantServiceImpl.java
- `createOAuthClient()`: Generates a cryptographically secure random string using `SecretGenerator`.
  Hashes it using BCrypt before storing in `OAuthClient` table. Returns plain text to caller.
- `regenerateClientSecret()`: Revokes old client, creates new client, revokes all active
  access tokens linked to the old client.
- `assignActsToTenant()`: Creates `TenantActAssignment` mappings.

### ChangeLogInterceptor.java
Evidence: interceptor/ChangeLogInterceptor.java
- INTERCEPTOR PATTERN: `@AroundInvoke` logic applied to service methods annotated with `@ChangeLogged`.
- LOGIC: Checks if method name starts with `create`, `update`, `delete`, `assign`, `remove`.
  If so, extracts the entity ID via reflection (`getId()`) or parameter scanning.
- PURPOSE: Inserts a record into the `change_logs` table.
- WHY: This is the backbone of the delta-sync architecture. Instead of `compliance-core`
  polling all data, it polls `mdm-subscriptions` asking "what changed since sequence X?".
  This interceptor generates the audit trail that makes sequence-based sync possible.

================================================================================
## 5. SECURITY ANALYSIS (DEEP DIVE)
================================================================================

### 5.1 Authorization Middleware
Evidence: security/AuthorizationMiddleware.java
ROLES:
- `READ_ONLY`: GET access to all content namespaces.
- `SME` (Subject Matter Expert): READ_ONLY + PATCH access to `/api/v1/obligations/**`.
- `ADMIN`: Full CRUD access to all `/api/v1/**` endpoints.

### 5.2 OAuth 2.0 Authorization Server Implementation
Evidence: serviceimpl/OAuthServiceImpl.java
- MDM acts as its own Identity Provider for machine-to-machine communication.
- Implements `client_credentials` grant type.
- Access tokens are JWTs.

================================================================================
## 6. REPOSITORY ANALYSIS
================================================================================

### LegalDocumentRepository.java
Evidence: repository/LegalDocumentRepository.java
- Extensive use of Native SQL Queries instead of HQL.
- WHY NATIVE SQL?: The code explicitly comments: "Use native SQL to avoid 'operator does not exist: document_type_enum = character varying'". Hibernate has trouble binding Java enums to PostgreSQL custom ENUM types.
- Traversal logic: Traverses tree hierarchies up to the root Act (`findRootActId`) to ensure obligations are mapped to the correct top-level legislation.

================================================================================
## 7. CONFIGURATION ANALYSIS
================================================================================

FILE: application-dev.properties
DATABASE: `jdbc:postgresql://localhost:5432/mdm_db`
- Unique database separate from `compliance_dev`.
- `quarkus.hibernate-orm.database.generation=none` indicates schema is managed externally
  (likely by `mdm-initial-data`).

================================================================================
END OF MDM-CORE ANALYSIS
================================================================================
