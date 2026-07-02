================================================================================
INTERVIEW SAFE ANSWERS: CODE-EVIDENCE BASED
================================================================================
ROLE: Backend/Distributed Systems Engineer
RULE: Strict adherence to repository facts. No unverified claims of architecture ownership.
================================================================================

--------------------------------------------------------------------------------
TOPIC 1: PROJECT OVERVIEW
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"The team built a microservices-based B2B SaaS platform using Quarkus and PostgreSQL. We structured it around two isolated domains: an MDM (Master Data Management) global repository for legal rules, and a Compliance Execution domain where individual tenants manage their specific automated tasks."

2. AGGRESSIVE FOLLOW-UP: 
"Why physically separate the databases instead of just using tenant schemas?"

3. SAFE FOLLOW-UP ANSWER: 
"Decoupling the databases prevents heavy tenant operations—like running complex Quartz task generation—from causing lock contention or performance degradation on the central legal catalog. It does require us to maintain a dedicated synchronization service (`mdm-subscriptions`), but the isolation trade-off is worth it for stability."

4. WHAT NOT TO CLAIM: 
- Do not claim you architected the microservice boundaries from scratch (unless applying for Principal/Staff).
- Do not claim knowledge of the exact cloud infrastructure (AWS/GCP), as the repo only provides Kubernetes and Docker properties.

5. CONFIDENCE LEVEL: HIGH

--------------------------------------------------------------------------------
TOPIC 2: COMPLIANCE CORE
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"The `compliance-core` service handles the primary execution logic for tenants. It relies on REST endpoints for the frontend and heavily utilizes Quartz schedulers for recurring compliance task generation based on legal deadlines."

2. AGGRESSIVE FOLLOW-UP: 
"How do you prevent out-of-memory errors when processing and generating thousands of tasks?"

3. SAFE FOLLOW-UP ANSWER: 
"The codebase manages this by establishing strict transaction boundaries using `@Transactional(REQUIRES_NEW)` and processing records in paginated batches. Instead of loading an entire tenant's workload into a single Hibernate session, we commit in chunks."

4. WHAT NOT TO CLAIM: 
- Do not claim the system uses Kafka or RabbitMQ for event-driven task generation. The code strictly utilizes Quartz scheduling for internal workflows.

5. CONFIDENCE LEVEL: HIGH

--------------------------------------------------------------------------------
TOPIC 3: AUTHENTICATION
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"We centralized IAM in the `compliance-auth` service. It issues an RSA-signed asymmetric JWT that is stored in an HttpOnly cookie. The other microservices utilize a `CookieAuthRequestFilter` to verify the public key signature statelessly."

2. AGGRESSIVE FOLLOW-UP: 
"If token validation is stateless, how do you handle token revocation or forced logouts?"

3. SAFE FOLLOW-UP ANSWER: 
"The architecture mitigates this by keeping the JWT lifespan very short (e.g., 15 minutes). For longer sessions, the database stores a persistent Refresh Token. Upon explicit logout, the client drops the cookie and we invalidate the refresh token in the database."

4. WHAT NOT TO CLAIM: 
- Do not claim we use a dedicated API Gateway (like Kong or Apigee) for centralized token validation. The validation happens locally within each microservice via Quarkus request filters.

5. CONFIDENCE LEVEL: HIGH

--------------------------------------------------------------------------------
TOPIC 4: MDM (MASTER DATA MANAGEMENT)
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"The `mdm-core` service acts as the source of truth for legal mutations. We capture changes using a custom Aspect-Oriented `@ChangeLogged` interceptor, which writes the delta to a `change_logs` table to establish a trail for downstream replication."

2. AGGRESSIVE FOLLOW-UP: 
"Why use an application-level interceptor instead of database triggers for logging?"

3. SAFE FOLLOW-UP ANSWER: 
"The interceptor allows us to easily capture the application-level context—such as the user's identity and specific business logic context—which is much harder to pass down into a generic PostgreSQL trigger."

4. WHAT NOT TO CLAIM: 
- Do not claim the team uses Debezium or Kafka CDC for MDM tracking. The code strictly relies on AOP interceptors and polling.

5. CONFIDENCE LEVEL: HIGH

--------------------------------------------------------------------------------
TOPIC 5: AI INTEGRATION
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"We offload LLM processing to `compliance-ai`. To handle evidence matching securely, we implemented a metadata-only ranking approach with Claude. Instead of sending raw PDFs, we send extracted document summaries and keywords to be ranked against task requirements."

2. AGGRESSIVE FOLLOW-UP: 
"Why not use Vector Embeddings (RAG) for matching documents to tasks?"

3. SAFE FOLLOW-UP ANSWER: 
"Compliance nuances, especially dates (e.g., 'March 2024' vs 'March 2025'), are often too close in vector space, causing false positives. By passing metadata directly into the LLM prompt, we leverage the model's logical reasoning over strict temporal requirements."

4. WHAT NOT TO CLAIM: 
- Do not claim we fine-tuned our own LLM or host models locally. The codebase explicitly integrates with Claude.

5. CONFIDENCE LEVEL: HIGH

--------------------------------------------------------------------------------
TOPIC 6: DATABASE
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"We use PostgreSQL databases (`compliance_dev` and `mdm_dev`). To manage schemas safely, we created dedicated Liquibase microservices (`compliance-initial-data`, `mdm-initial-data`) to execute migrations before the main application nodes boot."

2. AGGRESSIVE FOLLOW-UP: 
"Why isolate Liquibase into separate services instead of running migrations on application boot?"

3. SAFE FOLLOW-UP ANSWER: 
"Because multiple Quarkus nodes starting simultaneously with `migrate-at-start=true` can cause severe lock contention or split-brain scenarios on the `DATABASECHANGELOG` table. Isolating it to an init-container pattern guarantees schema stability."

4. WHAT NOT TO CLAIM: 
- Do not claim the use of NoSQL databases, sharding, or schema-per-tenant architectures. The properties files explicitly show shared PostgreSQL JDBC URLs.

5. CONFIDENCE LEVEL: HIGH

--------------------------------------------------------------------------------
TOPIC 7: SCHEDULERS
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"The system utilizes Quartz Scheduler running in clustered mode, backed by PostgreSQL. This ensures jobs like task generation or MDM replication execute exactly once across the distributed cluster."

2. AGGRESSIVE FOLLOW-UP: 
"How exactly does clustered Quartz prevent duplicate job execution?"

3. SAFE FOLLOW-UP ANSWER: 
"It uses the database's `QRTZ_LOCKS` tables to acquire a pessimistic lock (`SELECT FOR UPDATE`) on the job trigger. The node that successfully acquires the lock fires the job, while the others yield."

4. WHAT NOT TO CLAIM: 
- Do not claim we use external orchestration tools like Temporal, AWS EventBridge, or Celery.

5. CONFIDENCE LEVEL: HIGH

--------------------------------------------------------------------------------
TOPIC 8: SECURITY
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"We enforce security at multiple layers: tenant data isolation is maintained via application-level multi-tenancy (tenant_id). Service-to-service interactions, like the tenant fetching data from MDM, are secured via an OAuth2 `client_credentials` flow."

2. AGGRESSIVE FOLLOW-UP: 
"If multi-tenancy is application-level, how do you mathematically guarantee a bug won't leak data across tenants?"

3. SAFE FOLLOW-UP ANSWER: 
"While we cannot eliminate all bug risk, we mitigate it heavily by tying the `tenant_id` context extraction directly to the authenticated JWT. All ORM queries and repository methods automatically append the contextual `tenant_id` to prevent cross-tenant queries."

4. WHAT NOT TO CLAIM: 
- Do not claim we use separate physical databases per tenant or Row-Level Security (RLS) in Postgres. The schema explicitly relies on foreign keys in shared tables.

5. CONFIDENCE LEVEL: HIGH

--------------------------------------------------------------------------------
TOPIC 9: SCALABILITY
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"To synchronize the central MDM database to thousands of tenants, the `mdm-subscriptions` service relies on a cursor-based, chunked polling architecture. `SnapshotJobs` paginate the heavy initial data load, and `ChangeJobs` chunk the delta updates."

2. AGGRESSIVE FOLLOW-UP: 
"Why use polling instead of pushing updates from MDM to tenants via WebSockets or Webhooks?"

3. SAFE FOLLOW-UP ANSWER: 
"Polling provides essential built-in backpressure. A tenant's database pulls chunks only as fast as its local resources can process them. A push model could cause Out-Of-Memory errors on the tenant side if a massive legal update occurs simultaneously."

4. WHAT NOT TO CLAIM: 
- Do not claim Kafka handles the MDM-to-Tenant replication. The code explicitly shows the tenant utilizing REST endpoint polling (`/jobs/consume`).

5. CONFIDENCE LEVEL: HIGH

--------------------------------------------------------------------------------
TOPIC 10: PRODUCTION ISSUES
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"A known architectural constraint is token expiration during long MDM synchronization jobs. Because the JWT lifespan is intentionally short, a large synchronization payload might trigger a 401 Unauthorized mid-flight."

2. AGGRESSIVE FOLLOW-UP: 
"How is this mitigated in the system?"

3. SAFE FOLLOW-UP ANSWER: 
"The client logic must trap the 401 status, utilize the Refresh Token to obtain a new access token, and then resume pulling data exactly from the last acknowledged sequence cursor."

4. WHAT NOT TO CLAIM: 
- Do not invent production outage "war stories" that cannot be verified by the code. Keep the focus strictly on architectural edge cases.

5. CONFIDENCE LEVEL: MEDIUM (Derived from architectural constraints, not outage logs).

--------------------------------------------------------------------------------
TOPIC 11: IMPROVEMENTS
--------------------------------------------------------------------------------
1. SAFE ANSWER: 
"A significant improvement we could implement today is replacing the application-level `@ChangeLogged` AOP interceptor with a true CDC tool like Debezium reading directly from the PostgreSQL WAL."

2. AGGRESSIVE FOLLOW-UP: 
"Why introduce the operational complexity of Debezium when the AOP interceptor already works?"

3. SAFE FOLLOW-UP ANSWER: 
"The interceptor only catches changes routed through the application's service layer. If a DBA runs a raw SQL `UPDATE` directly on the database to fix a bug, the interceptor misses it, resulting in replica drift. Debezium guarantees 100% capture at the storage level."

4. WHAT NOT TO CLAIM: 
- Do not claim that you actively started or completed a migration to Debezium. Present it strictly as a technical recommendation for future scaling.

5. CONFIDENCE LEVEL: HIGH
================================================================================
END OF INTERVIEW SAFE ANSWERS
================================================================================
