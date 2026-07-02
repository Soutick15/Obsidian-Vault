================================================================================
02_COMPLIANCE-AUTH FORENSIC ANALYSIS
SERVICE: compliance-auth
PORT: 8085
FRAMEWORK: Quarkus 3.30.6 + Java 21
DATABASE: compliance_dev (Azure PostgreSQL, SHARED with core/ai)
================================================================================

================================================================================
## 1. SERVICE OVERVIEW
================================================================================

PURPOSE:
Dedicated identity provider and authentication microservice for the NyAi platform.
Handles user login, registration, token issuance, refresh token management,
and user CRUD operations.

BUSINESS RESPONSIBILITY:
- Issuing JWT access and refresh tokens.
- Secure storage of passwords using BCrypt.
- Session management (login/logout/refresh).
- User profile and credential management.
- Multi-tenant entity resolution during registration.

WHY THIS SERVICE EXISTS:
Isolates security perimeters. By separating authentication from core business
logic, the platform can scale auth independently, manage secrets securely,
and keep the public-facing login endpoints decoupled from internal compliance APIs.

PROBLEM SOLVED:
Provides a central source of truth for identity. Prevents other services from
needing to manage password hashing or token generation.

================================================================================
## 2. PACKAGE ANALYSIS
================================================================================

### Package: com.nyai.config
- AppConfig.java — General configuration properties.

### Package: com.nyai.controller
- auth/AuthController.java — Handles login, logout, refresh, register, and /me endpoints.
- UserResource.java — CRUD operations for users and department assignments.

### Package: com.nyai.dto
- auth/LoginRequest, RegisterRequest, RefreshTokenRequest, TokenResponse, CurrentUserResponse
- UserDto, UserCreateRequest, UserUpdateRequest

### Package: com.nyai.entity
- RefreshToken.java — Tracks long-lived refresh tokens with revocation support.
- User.java — Core identity entity.
- Role.java, UserRole.java — RBAC role definitions.
- Tenant.java, BusinessEntity.java, Department.java, Task.java — Shared entity definitions (duplicated or shared JPA mappings for the shared database).

### Package: com.nyai.repository
- RefreshTokenRepository.java
- UserRepository.java
- RoleRepository.java
- TenantRepository.java, BusinessEntityRepository.java, DepartmentRepository.java

### Package: com.nyai.security
- JwtService.java — JWT generation (RSA Private Key) and validation.
- CookieAuthRequestFilter.java — Request interceptor for token extraction.
- PasswordService.java — BCrypt hashing wrapper.
- RolePermissionConfig.java — Role matrix (slightly different from core, focuses on core/evidence paths).
- PermissionFilter.java, SecurityUtils.java, AuthenticatedUser.java

### Package: com.nyai.service
- AuthService.java & impl/AuthServiceImpl.java — Core authentication logic.
- UserService.java — User management logic.

================================================================================
## 3. CONTROLLER ANALYSIS — CRITICAL ENDPOINTS
================================================================================

### AuthController.java — /v1/auth
Evidence: controller/auth/AuthController.java

┌──────────────┬──────────┬─────────────────────────────────────┬──────────────────────┐
│ Endpoint     │ Method   │ Purpose                             │ Key Logic            │
├──────────────┼──────────┼─────────────────────────────────────┼──────────────────────┤
│ /login       │ POST     │ Authenticate user                   │ Validates password,  │
│              │          │                                     │ issues JWT + Cookie  │
│ /register    │ POST     │ Register new user/tenant            │ Resolves SaaS tenant,│
│              │          │                                     │ hashes password      │
│ /refresh     │ POST     │ Issue new access token              │ Validates refresh    │
│              │          │                                     │ token, revokes old   │
│ /logout      │ POST     │ Invalidate session                  │ Deletes refresh token│
│              │          │                                     │ clears cookie        │
│ /me          │ GET      │ Get current user profile            │ Extracts from JWT    │
└──────────────┴──────────┴─────────────────────────────────────┴──────────────────────┘

SECURITY:
- /login, /register, /refresh, /logout are annotated with @PermitAll.
- /login and /register return HTTP response with `Set-Cookie: access_token=...; HttpOnly; Path=/`

### UserResource.java — /v1/core/users
Evidence: controller/UserResource.java

Endpoints:
  POST / — Create user (Admin operation)
  GET / — List all users
  GET /{id}/detail — Get specific user
  PUT /{id} — Update user
  DELETE /{id} — Delete user
  GET /by-department/{departmentId} — Get users by department
  PUT /{id}/change-department — Reassign department
  PUT /{id}/change-password — Update password (requires newPassword in body)
  GET /with-tasks — Get users with their assigned tasks

================================================================================
## 4. SERVICE ANALYSIS (DEEP DIVE)
================================================================================

### AuthServiceImpl.java
Evidence: service/impl/AuthServiceImpl.java

LOGIN FLOW:
  1. Find user by email.
  2. Check if user isActive and tenant isActive.
  3. Verify password via BCrypt (PasswordService).
  4. Update lastLoginAt timestamp.
  5. Generate Access Token (1 hour) and Refresh Token (7 days).
  6. Persist RefreshToken entity with IP Address and User-Agent.

REGISTER FLOW:
  1. Check if email already exists (ConflictException).
  2. Resolve SaaS Tenant (defaults to "default" tenant, meaning multi-tenancy onboarding requires a default tenant to exist).
  3. Resolve Entity:
     - If entityId provided: link to existing entity.
     - If entityName provided: create new BusinessEntity.
  4. Assign default role (ADMIN).
  5. Hash password and persist User.
  6. Issue tokens.

REFRESH FLOW:
  1. Lookup RefreshToken by token string.
  2. Validate expiry and revoked status.
  3. Validate user and tenant active status.
  4. Revoke the used refresh token (token rotation).
  5. Issue new access and refresh tokens.

LOGOUT FLOW:
  1. Get current userId and tenantId from security context.
  2. Delete refresh token from database.
  3. Controller clears the browser cookie.

================================================================================
## 5. SECURITY ANALYSIS (DEEP DIVE)
================================================================================

### 5.1 JWT Generation (JwtService.java)
- SIGNING: Uses RSA Private Key (`keys/privateKey.pem`).
- ISSUER: `compliance-service`
- CLAIMS:
  - `sub`: userId
  - `email`, `firstName`, `lastName`
  - `entityId`, `tenantId`, `tenantActive`
  - `groups`: User roles (from `user.getRoles()` fallback to `user.getRole()`)
- EXPIRY: Access (3600s), Refresh (604800s).

### 5.2 Token Transport
- Primary transport is HttpOnly Cookies.
- AuthController `buildAccessTokenCookie()` sets `authCookieSecure=false` (dev environment).
- Cookie is intercepted by `CookieAuthRequestFilter` and translated to `Authorization: Bearer <token>` for standard JAX-RS processing.
- CROSS-DOMAIN RISK: If frontend and backend are on different domains, cookies won't be sent unless CORS and SameSite are configured correctly.
  Evidence: `application-dev.properties` -> `quarkus.http.same-site-cookie.access_token=none`

### 5.3 Password Hashing
- BCrypt implementation (org.mindrot:jbcrypt).
- Evidence: PasswordService.java handles `hashPassword` and `verifyPassword`.

================================================================================
## 6. ENTITY ANALYSIS
================================================================================

### User Entity
TABLE: users
FIELDS: id, email (unique), passwordHash, firstName, lastName, phone, role, isActive, lastLoginAt.
RELATIONSHIPS:
  - ManyToOne -> Tenant, BusinessEntity, Department
  - ManyToMany -> Role (user_roles table)

### RefreshToken Entity
TABLE: refresh_tokens
FIELDS: id, token (unique), user_id, expires_at, created_at, revoked, revoked_at, revoked_by, ip_address, user_agent, tenant_id.
INDEXES: token, user_id, tenant_id.
BUSINESS MEANING: Enables stateful session revocation despite stateless JWTs. By rotating tokens on refresh, it mitigates token theft.

================================================================================
## 7. CONFIGURATION ANALYSIS
================================================================================

FILE: application-dev.properties
KEY CONFIGURATIONS:
  quarkus.http.port=8085
  quarkus.datasource.jdbc.url=jdbc:postgresql://nyai-metadata-db-dev.postgres.database.azure.com:5432/compliance_dev
  quarkus.hibernate-orm.database.generation=none (schema managed externally)
  smallrye.jwt.sign.key.location=keys/privateKey.pem
  mp.jwt.verify.publickey.location=keys/publicKey.pem
  auth.cookie.name=access_token
  quarkus.http.cors.origins=http://localhost:3000,http://127.0.0.1:3000,http://localhost:4200
  quarkus.http.cors.access-control-allow-credentials=true

SHARED DATABASE AWARENESS:
  This service connects to the EXACT same database schema (`compliance_dev`) as `compliance-core`.
  Evidence: The JDBC URL is identical to `compliance-core`.

================================================================================
## 8. SCHEDULER & INTEGRATION ANALYSIS
================================================================================

SCHEDULERS: None found. Token cleanup is likely handled via expiration or manual DB purges, or left orphaned if revoked.
INTEGRATIONS: None. `compliance-auth` has no external dependencies other than the shared PostgreSQL database. It operates entirely autonomously.

================================================================================
END OF COMPLIANCE-AUTH ANALYSIS
================================================================================
