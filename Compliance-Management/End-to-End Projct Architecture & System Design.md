## 1. Executive Summary
ComplianceManagementSystem is a sophisticated, AI-powered Compliance and Master Data Management (MDM) platform. The system is designed to provide centralized compliance tracking, intelligent risk assessment, and secure distribution of legal/compliance obligations to multiple tenants (cloud-hosted or on-premise). 

It employs a microservices architecture built for high performance, cloud-native scalability, and rapid execution using modern Java and Quarkus.

## 2. Global Technology Stack
Across all microservices, ComplianceManagementSystem standardizes on a highly modern, cloud-native stack:
- **Language**: Java 21 (leveraging modern LTS features)
- **Framework**: Quarkus 3.30.6 (optimized for Kubernetes/Cloud)
- **Database**: PostgreSQL 18 (for robust relational data persistence)
- **Graph/AI DB**: FalkorDB (used specifically in the AI service for graph-based logic)
- **Native Compilation**: GraalVM / Mandrel 21 (compiles Java directly to native machine code for instant startup and low memory footprint)
- **Containerization**: Docker & Docker Compose

## 3. Microservices Landscape

The system ComplianceManagementSystemivided into two primary domains: **Compliance (Tenant-facing)** and **MDM (Master Data Management)**.

### 3.1. Compliance Domain
These services handle the tenant-specific workflows, users, and intelligent insights.

#### A. `compliance-core` (Main Tenant Service)
- **Role**: The central service for tenant compliance management.
- **Responsibilities**: Manages users, organizations, and the core compliance workflows. 
- **Key Endpoints**:
  - `GET /api/v1/users` - List users
  - `POST /api/v1/users` - Create user
  - `PUT /api/v1/users/{id}` - Update user
  - `DELETE /api/v1/users/{id}` - Delete user
- **Note**: It relies on a separate initial-data service (`compliance-initial-data`) to populate its default database state.

#### B. `compliance-auth` (Authentication & Security Service)
- **Role**: Centralized identity and access management.
- **Responsibilities**: Generates JWT tokens, manages Role-Based Access Control (RBAC), and handles session lifecycles.
- **Key Endpoints**:
  - `POST /api/v1/auth/login` - User login
  - `POST /api/v1/auth/register` - User registration
  - `POST /api/v1/auth/refresh` - Refresh JWT token
  - `GET /api/v1/auth/validate` - Validate JWT token

#### C. `compliance-ai` (AI & Intelligence Service)
- **Role**: The brain of the platform.
- **Responsibilities**: Provides AI-powered compliance analysis, intelligent insights, risk assessments, and automated recommendations. It utilizes Machine Learning and Graph-based analysis (backed by FalkorDB).
- **Key Endpoints**:
  - `POST /api/v1/compliance-ai/analyze` - Analyze compliance state
  - `POST /api/v1/compliance-ai/risk-assessment` - Perform risk assessment
  - `GET /api/v1/compliance-ai/recommendations` - Get automated AI recommendations

### 3.2. MDM (Master Data Management) Domain
These services manage the global repository of Indian compliance data and its distribution to individual tenants.

#### D. `mdm-core` (Central Repository)
- **Role**: The single source of truth for global compliance data.
- **Responsibilities**: Stores the master hierarchy of legal packages, acts, rules, regulations, and actionable tasks. It generates an append-only `change_log` whenever legal obligations change.
- **Data Structure**:
  - `Packages` (e.g., Labour Law)
    - `Acts` (e.g., The Factories Act, 1948)
      - `Rules & Regulations`
        - `Tasks` (actionable items like severity, penalties, due dates)

#### E. `mdm-subscriptions` (Distribution Layer)
- **Role**: The critical bridge between `mdm-core` and external Compliance Tenants.
- **Architecture Highlights**:
  - **Shared Database**: It sits on the exact same database instance as `mdm-core`, reading core tables directly via SQL joins rather than making expensive HTTP calls. It has read/write ownership of its own tables (`subscriptions`, `subscription_packages`, `subscription_cursors`, `snapshot_jobs`).
  - **Pull-Only Model**: MDM is cloud-hosted while tenants can be on-premise. To solve firewall constraints, MDM NEVER pushes data. Tenants must pull (poll) data from `mdm-subscriptions`.
- **Workflow & Lifecycle**:
  1. **Phase 1: Tenant Onboarding**: Admin registers a tenant; OAuth credentials are provided.
  2. **Phase 2: Snapshotting**: Tenant subscribes to a package. A background worker locks the current `sequence_number` and chunks massive amounts of data for the tenant to download entirely (the "Snapshot").
  3. **Phase 3: Infinite Delta Polling**: Tenant periodically polls `GET /subscription/changes`. The service uses strict integer sequence numbers (not timestamps, to avoid clock skew and race conditions) to fetch exactly what changed since the tenant's last poll.
- **Change Types Contract**: 
  - `created`: Tenant inserts new entity.
  - `updated`: Tenant updates entity in place.
  - `superseded`: A critical legal change (e.g., penalty increase). Tenant marks old task as superseded and inserts the new one.
  - `deprecated`: No longer in force.
  - `deleted`: Admin data correction.

## 4. System Design & Data Flow Highlights

### Database Interaction (The "Shared DB" Pattern)
Instead of typical microservice network chattiness, `mdm-subscriptions` and `mdm-core` share a database. 
- `mdm-core` handles writes to the master data (`acts`, `packages`, `change_log`).
- `mdm-subscriptions` treats master tables as Read-Only, joining them with its own Read/Write state tables (`subscription_cursors`).
- This guarantees maximum performance during heavy synchronous operations and complex aggregations.

### Resilient Synchronization (Sequence Numbers)
Data synchronization between MDM and Tenants strictly uses a `BIGINT sequence_number` instead of `updated_at` timestamps. This guarantees:
- No missed records due to load-balancer clock skew.
- No race conditions from concurrent updates in the same millisecond.
- Tenants can disconnect for months and seamlessly resume exactly where they left off by sending their `last_acked_sequence`.

### AI & Graph Integration
By offloading complex relationship mapping to FalkorDB in `compliance-ai`, the system can map abstract legal risks to concrete business operations using graph traversals, allowing the AI to output highly contextualized recommendations rather than generic advice.

## 5. Development & Deployment Workflow
- The platform uses a strictly enforced CI/CD model. Developers merge directly to a `build` branch to test in staging.
- All code must adhere to 80% test coverage and utilize GraalVM native image builds to ensure services can scale from 0 to 1 almost instantly in Kubernetes environments.

## 6. Microservice Deep Dives

### 6.1. mdm-core (Master Data Management Central Repository)

#### Overview & Role
`mdm-core` serves as the global single source of truth for all compliance and legal data (Packages, Acts, Rules, Regulations, Tasks). It is strictly responsible for ingesting, managing, and versioning legal updates. It does not handle tenant-specific data.

#### Architecture & Workflow
- **Standard Layered Architecture**: Uses a classic Controller -> Service -> Repository layer structure (`controller`, `service`, `repository`, `model` packages).
- **Versioning Engine**: When a legal act or rule is modified, `mdm-core` generates an append-only `change_log`. It manages strict `sequence_number` generation instead of relying on `updated_at` timestamps.
- **Data Persistence Strategy**: Utilizes Hibernate ORM with Panache for interaction with PostgreSQL. 

#### Tools and Technologies Used
*Note: While many enterprise architectures rely heavily on Kafka/RabbitMQ or FeignClients for inter-service communication, ComplianceManagementSystem specifically designed `mdm-core` to avoid these for data distribution to maximize performance.*
- **Java 21 & Quarkus 3.30.6**: For high-performance, cloud-native execution.
- **GraalVM (Mandrel 25)**: Compiles the service into a native binary for near-instant startup.
- **PostgreSQL 18**: Primary relational store. It **shares** this database instance with `mdm-subscriptions`.
- **FalkorDB**: Configured for graph-based logic (via `application.properties`).
- **Communication Pattern (No Feign/Kafka)**: Instead of using a `FeignClient` to call `mdm-subscriptions` or pushing messages onto a `Kafka/RabbitMQ` topic when data changes, `mdm-core` writes directly to the shared database. `mdm-subscriptions` then reads this via SQL joins. This eliminates network HTTP overhead and the operational complexity of a message broker for enormous legal datasets.
- **Monitoring & Observability**: Micrometer with Prometheus, and OpenAPI/Swagger.

#### Common Interview Questions (Challenges & Design Decisions)

**Q1: Why didn't you use Kafka or RabbitMQ to publish legal changes to tenants?**
*Answer:* Using a message broker for massive initial data syncs (Snapshots) and subsequent deltas is an anti-pattern for huge relational datasets. A tenant subscribing to a "Labour Law" package might need 50,000 records immediately. Pushing 50k messages through Kafka per tenant is inefficient. Instead, we used a **Shared Database + Pull-Polling** model. Tenants pull their delta changes via `mdm-subscriptions` using sequence numbers, avoiding broker overhead and ensuring zero dropped messages even if a tenant is offline for months.

**Q2: Since you didn't use FeignClient, how does `mdm-core` communicate with `mdm-subscriptions`?**
*Answer:* They communicate via the **Shared Database Pattern**. While sharing a DB between microservices is generally an anti-pattern, we implemented it strategically here (the "Data Pump" pattern). `mdm-core` owns the writes to the master tables. `mdm-subscriptions` only has Read access to the master tables but Write access to its own `subscription_cursors` table. This allows us to do a massive database `JOIN` between what changed in master data and what the tenant has already synced. Doing this via HTTP and Feign would be impossible or horribly slow.

**Q3: What were the main challenges you faced while developing `mdm-core`?**
*Answer:*
1. **Clock Skew & Race Conditions in Distributed Systems**: Initially, we might have used `updated_at` to track data changes. But in a clustered Kubernetes environment, clock skew between instances meant data could be missed by polling clients. We solved this by implementing strict, transactional `sequence_number` integers.
2. **Native Image Build Times vs Developer Experience**: Using GraalVM Mandrel provides amazing startup times (under 100ms), but the native compilation process is CPU/memory intensive and slow. We optimized this by heavily utilizing Quarkus Dev Mode (Hot Reload) during local development and strictly reserving native image builds for the final CI/CD staging/prod pipelines.

### 6.2. compliance-auth (Centralized Identity & Access Management)

#### Overview & Role
`compliance-auth` acts as the gatekeeper for the tenant-facing side of the application. It is strictly responsible for authenticating users, validating credentials, issuing JSON Web Tokens (JWTs), and managing Role-Based Access Control (RBAC).

#### Architecture & Workflow
- **Authentication Flow**: Users interact with the `AuthController` (e.g., login, register). The service hashes passwords using BCrypt (`PasswordService`) and verifies them against the PostgreSQL database.
- **Token Generation (Asymmetric)**: Upon successful login, `JwtService` generates a JWT. Crucially, this is done using **Asymmetric Encryption** (RSA). `compliance-auth` signs the token using a private key (`privateKey.pem`), utilizing BouncyCastle to parse the PKCS#1 format.
- **Secure Cookie Delivery**: To protect against Cross-Site Scripting (XSS), the token is not returned in the raw JSON body for local storage. Instead, custom filters (`CookieAuthRequestFilter` and `CookieEntityResolver`) inject the token into an `HttpOnly` cookie.
- **Granular RBAC**: The service goes beyond standard roles by implementing a granular permission system. It uses custom `@RequiresPermission` annotations parsed by a `PermissionFilter` and configured in `RolePermissionConfig`.

#### Tools and Technologies Used
- **Java 21 & Quarkus 3.30.6**: The core backend framework.
- **Quarkus Security & SmallRye JWT**: For security contexts and generating/validating standard JWTs.
- **jBCrypt**: For secure, salted password hashing.
- **BouncyCastle**: Specialized cryptography library used to securely parse PEM key files.
- **Hibernate ORM with Panache & PostgreSQL**: For user and role data persistence.
- **ModelMapper**: Used heavily in the DTO layer to map complex User and Auth entities to secure Data Transfer Objects.

#### Common Interview Questions (Challenges & Design Decisions)

**Q1: How do you secure your JWTs against token theft and tampering?**
*Answer:* We implemented two major security patterns. First, we use **Asymmetric Encryption** (RSA Public/Private Keys) rather than a shared symmetric secret (like HMAC). `compliance-auth` is the *only* service in the cluster that possesses the `privateKey.pem` required to forge a token. Other microservices (like `compliance-core`) only have the `publicKey.pem` which can only *verify* the token. Second, we deliver the JWT via an `HttpOnly` cookie (configured via `app.cookie.http-only=true`), which means malicious JavaScript running in the browser (XSS) cannot access the token.

**Q2: I see `compliance-auth` connects to the database, but Flyway migrations are explicitly disabled (`quarkus.flyway.migrate-at-start=false`). Why?**
*Answer:* This solves the "Multiple Masters" schema problem. Because both `compliance-auth` and `compliance-core` need access to the tenant `users` tables, having both services try to run Flyway migrations simultaneously during deployment would cause database locks or schema conflicts. We abstracted schema management out entirely. A dedicated service (`compliance-initial-data`) handles all Flyway migrations and initial seed data, while `auth` and `core` simply consume the schema.

**Q3: How does your Role-Based Access Control (RBAC) differ from standard Spring Security / Quarkus Security roles?**
*Answer:* Standard framework roles (like `@RolesAllowed("ADMIN")`) are often too coarse for a multi-tenant B2B platform. We needed to distinguish between a "System Admin" and a "Tenant Admin" who only has power over their specific organization. We built a custom `PermissionFilter` and `@RequiresPermission` annotation system (`RolePermissionConfig`). This intercepts the request, extracts the tenant ID from the JWT context, and verifies if the user's specific role maps to the requested permission *within that specific tenant*.

### 6.3. compliance-core (Main Tenant & Workflow Engine)

#### Overview & Role
`compliance-core` is the workhorse of the tenant-facing application. While `mdm-core` stores the global law, `compliance-core` handles how a specific tenant (company) interacts with that law. It manages tenant users, documents, organizational hierarchies, and the execution engine for compliance tasks.

#### Architecture & Workflow
- **Data Consumption (The Pull Model)**: It heavily utilizes background cron jobs (`SubscriptionSyncScheduler`, `SnapshotConsumptionScheduler`) to poll the `mdm-subscriptions` service. It pulls the latest legal data via Quarkus REST Clients and maps it into the tenant's local database.
- **Task & Rule Engine**: The service features a robust scheduling engine (`TaskGenerationScheduler`, `TaskRecurrenceScheduler`, `TaskOverdueScheduler`) that continuously monitors the legal data and the tenant's profile to automatically generate, assign, and track compliance tasks.
- **Document Processing Pipeline**: Tenants upload legal documents and proofs. The service intercepts these, performs OCR (Optical Character Recognition) to extract text, and uses NLP (Natural Language Processing) to match document contents against required compliance proofs.
- **AI Integration**: It acts as a bridge, securely passing complex tenant data to `compliance-ai` via a dedicated REST client (`ComplianceAiClient`) to get risk scores and automated recommendations.

#### Tools and Technologies Used
- **Java 21 & Quarkus 3.30.6**: Providing the core reactive engine and REST endpoints.
- **Quarkus Scheduler**: Manages the complex array of background chron jobs without needing external tools like Quartz.
- **Quarkus REST Client (Jackson)**: Provides declarative, type-safe HTTP clients to communicate with MDM and AI services.
- **Apache Tika & Tesseract OCR**: Used to extract raw text from uploaded tenant PDFs and images.
- **Apache Commons Text & WordNet (extJWNL)**: Provides NLP synonym mapping and Jaro-Winkler string similarity algorithms to intelligently match uploaded document text to legal requirements.
- **Eclipse Angus Mail**: Dynamic SMTP processing for sending overdue task reminders and system alerts.
- **FalkorDB**: Also integrated here to query tenant-specific compliance relationship graphs.

#### Common Interview Questions (Challenges & Design Decisions)

**Q1: How does `compliance-core` stay updated with the global MDM without creating tight coupling?**
*Answer:* We deliberately avoided tight coupling (like shared databases between MDM and Tenants) or pushing data via message brokers. Instead, `compliance-core` uses a resilient "Pull" architecture. Background schedulers (`SubscriptionSyncScheduler`) periodically poll the MDM's REST APIs using sequence numbers. This guarantees that if the tenant service goes down or loses network connectivity, it can simply resume polling exactly where it left off once it recovers, ensuring zero data loss.

**Q2: Dealing with documents and OCR can be very CPU intensive. How does that impact the API performance?**
*Answer:* Document processing (using Apache Tika and Tesseract) is naturally synchronous and blocks threads. To prevent this from degrading the main API's responsiveness, we offload document text extraction and NLP matching to background threads or asynchronous event buses within Quarkus. For massive enterprise documents, we chunk the processing or schedule it during off-peak hours using our robust Scheduler engine.

**Q3: Why build a custom Task Recurrence Scheduler instead of using a standard workflow engine like Camunda or Temporal?**
*Answer:* While Temporal or Camunda are excellent, incorporating them introduces massive infrastructural overhead and steep learning curves. Since Indian compliance laws have highly specific, heavily regulated recurrence patterns (e.g., "Must file within 15 days of the end of the financial quarter"), building a custom, highly-tuned Scheduler native to Quarkus allowed us to tie the task generation directly into the `sequence_number` changes from MDM, keeping the architecture much leaner and faster.

### 6.4. compliance-ai (The Intelligence & Analysis Engine)

#### Overview & Role
`compliance-ai` acts as the "Brain" of the platform. Rather than dealing with standard CRUD operations, this service is entirely dedicated to cognitive tasks: evaluating tenant compliance gaps, automatically matching uploaded documents (evidence) to legal requirements, answering compliance questionnaires, and providing risk analytics.

#### Architecture & Workflow
- **Metadata-Driven Evidence Ranking (LLM Optimization)**: A major architectural highlight is the `ClaudeRankingService`. In traditional AI applications, processing 500-page PDFs requires chunking the text, storing it in a Vector Database (like Pinecone or Milvus), and performing cosine-similarity searches. Instead, ComplianceManagementSystem uses an optimized approach:
  1. `compliance-core` extracts text/metadata (Summary, Date, Keywords) using Apache Tika.
  2. `compliance-ai` takes *only* this metadata (about 200-300 characters per document) and passes it to Claude (Anthropic API).
  3. Claude looks at all candidate document summaries simultaneously and returns a ranked JSON array of the best evidence matches.
  *This eliminates the need for expensive Vector Databases, reduces LLM token costs drastically, and improves matching accuracy by giving the LLM full context.*
- **Graph-Based Compliance Traversal**: The service integrates with **FalkorDB** (a high-performance Graph Database) via `MaterializationSyncRunner`. Legal compliance is inherently graph-like (e.g., A Factory in Mumbai -> relates to -> Maharashtra State Law -> requires -> Form 11). By materializing this data into a Graph DB, the AI can execute rapid Cypher queries to deduce applicability and risk rather than doing dozens of complex SQL joins.
- **Gap Analysis & Questionnaires**: Features dedicated processors (`GapAnalysisService`, `QuestionnaireAiResolutionService`) that analyze a tenant's profile against the graph to automatically highlight missing compliance tasks.

#### Tools and Technologies Used
- **Java 21 & Quarkus 3.30.6**: Consistent with the global stack.
- **Anthropic Claude (via AiClientHelper)**: The primary Large Language Model used for decision-making and ranking, accessed via Quarkus REST clients.
- **FalkorDB (via Jedis client)**: Used for Graph Traversal and executing Cypher queries to map complex legal hierarchies to tenant operations.
- **Apache Tika**: Integrated for document processing capabilities.
- **PostgreSQL**: For storing AI processing states and cached gap analysis reports.

#### Common Interview Questions (Challenges & Design Decisions)

**Q1: Why didn't you use a Vector Database (like Pinecone) or RAG (Retrieval-Augmented Generation) for document matching?**
*Answer:* RAG and Vector DBs are great for "chat with your data," but they are actually poor at "ranking." If a tenant uploads 50 different "PF Challan" receipts, a vector similarity search will return all 50 as highly relevant because they contain the exact same keywords. By extracting metadata/summaries first and using Claude to rank them via a direct JSON prompt, the LLM can evaluate the *dates* and *context* of the documents simultaneously (e.g., "This challan is for March, but the task requires April"). It's significantly cheaper, faster, and much more accurate for strict compliance tasks.

**Q2: What is FalkorDB and why did you use it instead of sticking with PostgreSQL for everything?**
*Answer:* FalkorDB is a Graph Database. While PostgreSQL is excellent for transactional data, compliance applicability rules are essentially a massive web of relationships (e.g., "If Employee Count > 50 AND State = Karnataka -> Law X applies"). Querying this recursively in SQL is incredibly slow and complex. Using FalkorDB allows us to traverse these relationships using simple Cypher queries in milliseconds, which we then feed to the AI for final analysis.

**Q3: How do you prevent the AI service from exposing sensitive cross-tenant data?**
*Answer:* Every API call to `compliance-ai` requires a JWT. Our `AiClientHelper` strictly injects the `tenant_id` into both the graph database queries and the LLM context prompts. The AI is structurally isolated; it can only query FalkorDB nodes that have a matching `tenant_id` edge, ensuring absolute data partitioning at the database level before the AI even sees the data.

## 7. Software Design Patterns & Architecture Patterns

Across the ComplianceManagementSystem platform, the codebase implements a mix of classic Gang of Four (GoF) design patterns and modern Microservice patterns to maintain clean, scalable, and resilient code.

### 7.1. Classic Software Design Patterns (GoF)

- **Filter / Interceptor Pattern (Chain of Responsibility)**: Extensively used for cross-cutting concerns like security. Classes such as `CookieAuthRequestFilter`, `PermissionFilter`, and `JwtAuthenticationFilter` implement the `ContainerRequestFilter` interface. They intercept HTTP requests to validate JWTs and enforce Role-Based Access Control (RBAC) before the request ever reaches the Controllers.
- **Observer Pattern (Event-Driven)**: Used heavily to decouple side effects from business logic. By utilizing Quarkus's `@Observes` annotation, classes like `EntityAuditObserver` listen for an `EntityAuditEvent` specifically during `TransactionPhase.AFTER_SUCCESS` to write audit logs asynchronously. `DatabaseLogSetup` observes `StartupEvent` to initialize connections.
- **Builder Pattern**: Utilized globally in the `dto` and `entity` layers. Relying heavily on Lombok's `@Builder` (e.g., `LegalFrameworkAlertDtoBuilder`, `RuleEvaluationResultDto.Builder`), it allows for the immutable construction of complex Data Transfer Objects without massive and brittle constructors.
- **Factory Pattern**: Found in places like `MdmClientFactory` inside `compliance-core`, which dynamically generates and configures the correct Quarkus REST Client instances for communicating with Master Data Management APIs.
- **Repository Pattern**: By leveraging Hibernate ORM with Panache, every microservice abstracts direct SQL queries into isolated `Repository` classes (e.g., `UserRepository`, `ActRepository`), keeping the `Service` layer strictly focused on business logic.

### 7.2. Microservice Architectural Patterns

- **Shared Database / Data Pump Pattern**: Used between `mdm-core` and `mdm-subscriptions`, and `compliance-auth` and `compliance-core`. While sharing databases is usually an anti-pattern, ComplianceManagementSystem uses it to avoid network latency and HTTP timeouts when querying and aggregating millions of compliance records.
- **Pull-Based Sync (Polling) Pattern**: Instead of pushing updates via a Pub-Sub Event Broker (like Kafka) which risks dropping messages if a tenant is offline, the system uses Schedulers (`SubscriptionSyncScheduler`) and strict `sequence_number` tracking so tenants can safely pull their own delta changes.
- **Externalized Schema Management Pattern**: Because `compliance-auth` and `compliance-core` share a database, having both run Flyway migrations would cause a "Multiple Masters" lock problem. Migrations are extracted into a dedicated, single-run service (`compliance-initial-data`), and auto-migration is turned off in the core services.
- **API Composition / Edge Auth Pattern**: `compliance-auth` acts as an edge identity provider using Asymmetric JWTs (Private Key signing). Other microservices only need the Public Key to independently verify requests, avoiding a network bottleneck of calling the Auth service for every single hop.

#### Common Interview Questions (Design Patterns)

**Q1: Looking at the microservices, why did you choose the Observer Pattern for auditing instead of just writing the audit log directly in the Service layer?**
*Answer:* Coupling audit logging directly into the business logic (e.g., a `UserService`) violates the Single Responsibility Principle and clutters the code. By using the Observer pattern (via Quarkus `@Observes`), the `UserService` just fires an `EntityAuditEvent`. The `EntityAuditObserver` listens for this and handles the logging. More importantly, we bind the observer to `TransactionPhase.AFTER_SUCCESS`, ensuring we never write a false audit log if the main database transaction ends up rolling back.

**Q2: You mentioned using the "Shared Database Pattern." In microservice architecture, sharing databases is universally considered a bad practice. Why did you break this rule?**
*Answer:* It's true that the "Database per Service" pattern ensures loose coupling. However, engineering is about trade-offs. In the MDM domain, a single tenant syncing a legal package might require aggregating 50,000+ relational records. If `mdm-subscriptions` had to fetch this via HTTP REST calls (Feign) from `mdm-core` or via a Kafka stream, the network overhead and serialization costs would cause timeouts and out-of-memory errors. By using the Shared DB (or "Data Pump") pattern, `mdm-subscriptions` can execute a highly optimized SQL `JOIN` at the database level, transforming a fragile 5-minute network operation into a resilient 50-millisecond query.

**Q3: How does the Filter/Interceptor pattern improve the security architecture of the application?**
*Answer:* Security should be declarative and central, not sprinkled throughout every Controller method. By implementing `ContainerRequestFilter` (like our `PermissionFilter`), we intercept the incoming HTTP request. The filter extracts the JWT, verifies the tenant context, and checks custom `@RequiresPermission` annotations on the target endpoint. If the user lacks the role, the filter rejects the request with a 403 Forbidden immediately. This ensures that a developer cannot accidentally expose an endpoint by forgetting to add a security check inside their method.
